from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.models import (
    Base,
    Category,
    ComboOffer,
    ComboOfferItem,
    Coupon,
    Customer,
    Inventory,
    Order,
    OrderItem,
    OrderStatusHistory,
    Product,
    ProductImage,
    ProductVariant,
)
from app.models.enums import (
    ComboRuleType,
    DiscountType,
    OrderStatus,
    PaymentStatus,
    ProductStatus,
    Weight,
)
from tests.conftest import TEST_DATABASE_URL, alembic_config


def make_product(db, slug="gongura-chicken") -> Product:
    cat = Category(slug=f"cat-{slug}", name="Non-Veg Pickles")
    db.add(cat)
    db.flush()
    p = Product(slug=slug, category_id=cat.id, name="Gongura Chicken Pickle", name_te="గోంగూర")
    db.add(p)
    db.flush()
    return p


def make_order(db, number="GG-0001") -> Order:
    c = Customer(mobile="9000000000", name="Test")
    db.add(c)
    db.flush()
    o = Order(
        order_number=number,
        customer_id=c.id,
        subtotal=Decimal("100.00"),
        total=Decimal("100.00"),
        ship_full_name="Test",
        ship_mobile="9000000000",
        ship_house="1",
        ship_street="Main St",
        ship_village_city="Rajahmundry",
        ship_district="East Godavari",
        ship_state="Andhra Pradesh",
        ship_pin_code="533101",
    )
    db.add(o)
    db.flush()
    return o


def test_metadata_has_expected_tables_and_no_cart_tables():
    tables = set(Base.metadata.tables)
    assert len(tables) == 19
    assert "carts" not in tables and "cart_items" not in tables  # decision D1


def test_no_float_columns_for_money():
    for table in Base.metadata.tables.values():
        for col in table.columns:
            assert col.type.__class__.__name__ not in {"Float", "REAL", "DOUBLE_PRECISION"}


def test_migration_matches_models(pg_engine):
    command.check(alembic_config(TEST_DATABASE_URL))  # raises if models drifted from migration


def test_pg_trgm_index_exists(pg_engine):
    names = {i["name"] for i in inspect(pg_engine).get_indexes("products")}
    assert "ix_products_name_trgm" in names


def test_defaults_and_relationships(db):
    p = make_product(db)
    assert p.status == ProductStatus.ACTIVE and p.badges == []
    v = ProductVariant(product_id=p.id, weight=Weight.G500, price=Decimal("350.00"))
    v.inventory = Inventory(quantity=10)
    db.add(v)
    db.flush()
    db.refresh(p)
    assert [x.weight for x in p.variants] == [Weight.G500]
    assert p.variants[0].inventory.reserved == 0
    assert p.created_at is not None and p.id is not None


def test_variant_unique_per_weight_and_price_checks(db):
    p = make_product(db)
    db.add(ProductVariant(product_id=p.id, weight=Weight.KG1, price=Decimal(1)))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(ProductVariant(product_id=p.id, weight=Weight.KG1, price=Decimal(2)))
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(ProductVariant(product_id=p.id, weight=Weight.G250, price=Decimal(-1)))
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # compare-at below price
        db.add(
            ProductVariant(
                product_id=p.id,
                weight=Weight.G250,
                price=Decimal(5),
                compare_at_price=Decimal(4),
            )
        )
        db.flush()


def test_money_is_exact_decimal(db):
    p = make_product(db)
    v = ProductVariant(product_id=p.id, weight=Weight.G250, price=Decimal("199.99"))
    db.add(v)
    db.flush()
    db.expire(v)
    assert v.price == Decimal("199.99") and isinstance(v.price, Decimal)


def test_inventory_cannot_reserve_more_than_stock(db):
    p = make_product(db)
    v = ProductVariant(product_id=p.id, weight=Weight.G250, price=Decimal(1))
    db.add(v)
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(Inventory(variant_id=v.id, quantity=2, reserved=3))
        db.flush()


def test_only_one_primary_image_per_product(db):
    p = make_product(db)
    db.add(ProductImage(product_id=p.id, url="a", is_primary=True))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(ProductImage(product_id=p.id, url="b", is_primary=True))
        db.flush()
    db.add(ProductImage(product_id=p.id, url="c", is_primary=False))
    db.flush()


def test_category_with_products_cannot_be_deleted(db):
    p = make_product(db)
    cat = db.get(Category, p.category_id)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.delete(cat)
        db.flush()


def test_order_defaults_unique_number_and_history(db):
    o = make_order(db)
    assert o.order_status == OrderStatus.PENDING
    assert o.payment_status == PaymentStatus.PENDING  # never auto-paid
    db.add(OrderStatusHistory(order_id=o.id, from_status=None, to_status=OrderStatus.PENDING))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():
        make_order(db)  # same order_number, same mobile -> customer unique fails first
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            Order(
                order_number="GG-0001",
                customer_id=o.customer_id,
                subtotal=Decimal(1),
                total=Decimal(1),
                ship_full_name="x",
                ship_mobile="9",
                ship_house="x",
                ship_street="x",
                ship_village_city="x",
                ship_district="x",
                ship_state="x",
                ship_pin_code="533101",
            )
        )
        db.flush()


def test_order_item_survives_variant_deletion_as_history(db):
    p = make_product(db)
    v = ProductVariant(product_id=p.id, weight=Weight.G500, price=Decimal("350.00"))
    db.add(v)
    o = make_order(db)
    db.flush()
    item = OrderItem(
        order_id=o.id,
        product_id=p.id,
        variant_id=v.id,
        product_name=p.name,
        weight=Weight.G500,
        unit_price=Decimal("350.00"),
        quantity=2,
        line_total=Decimal("700.00"),
    )
    db.add(item)
    db.flush()
    db.delete(v)
    db.flush()
    db.expire(item)
    assert item.variant_id is None
    assert item.unit_price == Decimal("350.00") and item.weight == Weight.G500


def test_order_item_quantity_must_be_positive(db):
    o = make_order(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            OrderItem(
                order_id=o.id,
                product_name="x",
                weight=Weight.G250,
                unit_price=Decimal(1),
                quantity=0,
                line_total=Decimal(0),
            )
        )
        db.flush()


def test_invalid_enum_value_rejected(db):
    o = make_order(db)
    with pytest.raises(IntegrityError), db.begin_nested():
        db.execute(Order.__table__.update().where(Order.id == o.id).values(payment_status="bogus"))


def test_coupon_constraints(db):
    db.add(Coupon(code="WELCOME10", type=DiscountType.PERCENT, value=Decimal(10)))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # duplicate code
        db.add(Coupon(code="WELCOME10", type=DiscountType.FIXED, value=Decimal(50)))
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # >100%
        db.add(Coupon(code="BAD", type=DiscountType.PERCENT, value=Decimal(101)))
        db.flush()
    now = datetime.now(UTC)
    with pytest.raises(IntegrityError), db.begin_nested():  # end before start
        db.add(
            Coupon(
                code="DATES",
                type=DiscountType.FIXED,
                value=Decimal(5),
                starts_at=now,
                ends_at=now - timedelta(days=1),
            )
        )
        db.flush()


def test_combo_rules(db):
    p = make_product(db)
    with pytest.raises(IntegrityError), db.begin_nested():  # any_n requires item_count
        db.add(ComboOffer(slug="bad", name="Bad", rule_type=ComboRuleType.ANY_N, price=Decimal(1)))
        db.flush()
    combo = ComboOffer(
        slug="any-3",
        name="Any 3",
        rule_type=ComboRuleType.ANY_N,
        item_count=3,
        price=Decimal(900),
    )
    db.add(combo)
    db.flush()
    db.add(ComboOfferItem(combo_id=combo.id, product_id=p.id))
    db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # duplicate product in combo
        db.add(ComboOfferItem(combo_id=combo.id, product_id=p.id))
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # neither product nor category
        db.add(ComboOfferItem(combo_id=combo.id))
        db.flush()
    with pytest.raises(IntegrityError), db.begin_nested():  # both
        db.add(ComboOfferItem(combo_id=combo.id, product_id=p.id, category_id=p.category_id))
        db.flush()
