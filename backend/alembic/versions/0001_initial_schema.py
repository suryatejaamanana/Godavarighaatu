"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-31 05:37:35.201629

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Trigram index on products.name (product search) needs pg_trgm; available on Supabase.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "admins",
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column(
            "role",
            sa.Enum(
                "super_admin",
                "manager",
                "staff",
                name="admin_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="staff",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admins")),
        sa.UniqueConstraint("email", name=op.f("uq_admins_email")),
    )
    op.create_table(
        "banners",
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("title_te", sa.String(length=200), nullable=True),
        sa.Column("subtitle", sa.String(length=300), nullable=True),
        sa.Column("subtitle_te", sa.String(length=300), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("mobile_image_url", sa.String(length=500), nullable=True),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name=op.f("ck_banners_date_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_banners")),
    )
    op.create_index(
        "ix_banners_is_active_sort_order", "banners", ["is_active", "sort_order"], unique=False
    )
    op.create_table(
        "categories",
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("name_te", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_te", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
    )
    op.create_table(
        "combo_offers",
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_te", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_te", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "rule_type",
            sa.Enum(
                "fixed_products",
                "any_n",
                name="combo_rule_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("item_count", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(rule_type = 'any_n' AND item_count IS NOT NULL AND item_count > 0) OR (rule_type = 'fixed_products' AND item_count IS NULL)",
            name=op.f("ck_combo_offers_item_count_matches_rule"),
        ),
        sa.CheckConstraint("price >= 0", name=op.f("ck_combo_offers_price_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_combo_offers")),
        sa.UniqueConstraint("slug", name=op.f("uq_combo_offers_slug")),
    )
    op.create_table(
        "coupons",
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "percent",
                "fixed",
                name="coupon_type",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "min_purchase", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False
        ),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type <> 'percent' OR value <= 100", name=op.f("ck_coupons_percent_at_most_100")
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name=op.f("ck_coupons_date_range"),
        ),
        sa.CheckConstraint("min_purchase >= 0", name=op.f("ck_coupons_min_purchase_non_negative")),
        sa.CheckConstraint(
            "usage_limit IS NULL OR usage_limit > 0", name=op.f("ck_coupons_usage_limit_positive")
        ),
        sa.CheckConstraint("used_count >= 0", name=op.f("ck_coupons_used_count_non_negative")),
        sa.CheckConstraint("value > 0", name=op.f("ck_coupons_value_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_coupons")),
        sa.UniqueConstraint("code", name=op.f("uq_coupons_code")),
    )
    op.create_table(
        "customers",
        sa.Column("mobile", sa.String(length=15), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customers")),
        sa.UniqueConstraint("mobile", name=op.f("uq_customers_mobile")),
    )
    op.create_table(
        "website_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_website_settings")),
        sa.UniqueConstraint("key", name=op.f("uq_website_settings_key")),
    )
    op.create_table(
        "addresses",
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("house", sa.String(length=120), nullable=False),
        sa.Column("street", sa.String(length=200), nullable=False),
        sa.Column("village_city", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("pin_code", sa.String(length=6), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_addresses_customer_id_customers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_addresses")),
    )
    op.create_index(op.f("ix_addresses_customer_id"), "addresses", ["customer_id"], unique=False)
    op.create_table(
        "orders",
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("coupon_id", sa.UUID(), nullable=True),
        sa.Column("coupon_code", sa.String(length=40), nullable=True),
        sa.Column(
            "order_status",
            sa.Enum(
                "pending",
                "confirmed",
                "processing",
                "packed",
                "shipped",
                "out_for_delivery",
                "delivered",
                "cancelled",
                "returned",
                name="order_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.Enum(
                "pending",
                "paid",
                "failed",
                "refunded",
                name="payment_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "discount_total", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False
        ),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("ship_full_name", sa.String(length=120), nullable=False),
        sa.Column("ship_mobile", sa.String(length=15), nullable=False),
        sa.Column("ship_email", sa.String(length=254), nullable=True),
        sa.Column("ship_house", sa.String(length=120), nullable=False),
        sa.Column("ship_street", sa.String(length=200), nullable=False),
        sa.Column("ship_village_city", sa.String(length=120), nullable=False),
        sa.Column("ship_district", sa.String(length=120), nullable=False),
        sa.Column("ship_state", sa.String(length=120), nullable=False),
        sa.Column("ship_pin_code", sa.String(length=6), nullable=False),
        sa.Column("delivery_instructions", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_total >= 0 AND discount_total <= subtotal",
            name=op.f("ck_orders_discount_range"),
        ),
        sa.CheckConstraint("subtotal >= 0", name=op.f("ck_orders_subtotal_non_negative")),
        sa.CheckConstraint("total >= 0", name=op.f("ck_orders_total_non_negative")),
        sa.ForeignKeyConstraint(
            ["coupon_id"],
            ["coupons.id"],
            name=op.f("fk_orders_coupon_id_coupons"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            name=op.f("fk_orders_customer_id_customers"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_orders")),
        sa.UniqueConstraint("order_number", name=op.f("uq_orders_order_number")),
    )
    op.create_index(op.f("ix_orders_coupon_id"), "orders", ["coupon_id"], unique=False)
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)
    op.create_index(
        "ix_orders_order_status_created_at", "orders", ["order_status", "created_at"], unique=False
    )
    op.create_index("ix_orders_payment_status", "orders", ["payment_status"], unique=False)
    op.create_index(op.f("ix_orders_ship_mobile"), "orders", ["ship_mobile"], unique=False)
    op.create_table(
        "products",
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("name_te", sa.String(length=200), nullable=True),
        sa.Column("short_description", sa.String(length=300), nullable=True),
        sa.Column("short_description_te", sa.String(length=300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_te", sa.Text(), nullable=True),
        sa.Column("ingredients", sa.Text(), nullable=True),
        sa.Column("ingredients_te", sa.Text(), nullable=True),
        sa.Column("preparation", sa.Text(), nullable=True),
        sa.Column("preparation_te", sa.Text(), nullable=True),
        sa.Column("storage_instructions", sa.Text(), nullable=True),
        sa.Column("storage_instructions_te", sa.Text(), nullable=True),
        sa.Column("shelf_life", sa.String(length=100), nullable=True),
        sa.Column(
            "badges",
            postgresql.ARRAY(sa.String(length=40)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "inactive",
                "archived",
                name="product_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="active",
            nullable=False,
        ),
        sa.Column("is_featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_best_seller", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_new_arrival", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sold_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("seo_title", sa.String(length=200), nullable=True),
        sa.Column("seo_description", sa.String(length=320), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("sold_count >= 0", name=op.f("ck_products_sold_count_non_negative")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_products_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("slug", name=op.f("uq_products_slug")),
    )
    op.create_index(
        "ix_products_category_id_status", "products", ["category_id", "status"], unique=False
    )
    op.create_index(
        "ix_products_name_trgm",
        "products",
        ["name"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_table(
        "combo_offer_items",
        sa.Column("combo_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(product_id IS NOT NULL) <> (category_id IS NOT NULL)",
            name=op.f("ck_combo_offer_items_product_xor_category"),
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_combo_offer_items_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_combo_offer_items_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["combo_id"],
            ["combo_offers.id"],
            name=op.f("fk_combo_offer_items_combo_id_combo_offers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_combo_offer_items_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_combo_offer_items")),
    )
    op.create_index(
        op.f("ix_combo_offer_items_category_id"), "combo_offer_items", ["category_id"], unique=False
    )
    op.create_index(
        op.f("ix_combo_offer_items_combo_id"), "combo_offer_items", ["combo_id"], unique=False
    )
    op.create_index(
        op.f("ix_combo_offer_items_product_id"), "combo_offer_items", ["product_id"], unique=False
    )
    op.create_index(
        "uq_combo_offer_items_combo_category",
        "combo_offer_items",
        ["combo_id", "category_id"],
        unique=True,
        postgresql_where=sa.text("category_id IS NOT NULL"),
    )
    op.create_index(
        "uq_combo_offer_items_combo_product",
        "combo_offer_items",
        ["combo_id", "product_id"],
        unique=True,
        postgresql_where=sa.text("product_id IS NOT NULL"),
    )
    op.create_table(
        "order_status_history",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column(
            "from_status",
            sa.Enum(
                "pending",
                "confirmed",
                "processing",
                "packed",
                "shipped",
                "out_for_delivery",
                "delivered",
                "cancelled",
                "returned",
                name="history_from_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            sa.Enum(
                "pending",
                "confirmed",
                "processing",
                "packed",
                "shipped",
                "out_for_delivery",
                "delivered",
                "cancelled",
                "returned",
                name="history_to_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("changed_by_admin_id", sa.UUID(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_admin_id"],
            ["admins.id"],
            name=op.f("fk_order_status_history_changed_by_admin_id_admins"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_status_history_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_status_history")),
    )
    op.create_index(
        op.f("ix_order_status_history_order_id"), "order_status_history", ["order_id"], unique=False
    )
    op.create_table(
        "payments",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=40), server_default="manual", nullable=False),
        sa.Column("method", sa.String(length=40), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "paid",
                "failed",
                "refunded",
                name="payments_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name=op.f("ck_payments_amount_non_negative")),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_payments_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
    )
    op.create_index(op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False)
    op.create_index(
        "ix_payments_provider_provider_reference",
        "payments",
        ["provider", "provider_reference"],
        unique=False,
    )
    op.create_table(
        "product_images",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("alt_text", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_images_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_images")),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"], unique=False)
    op.create_index(
        "uq_product_images_primary",
        "product_images",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_table(
        "product_variants",
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column(
            "weight",
            sa.Enum(
                "250g",
                "500g",
                "1kg",
                name="variant_weight",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("compare_at_price", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "compare_at_price IS NULL OR compare_at_price >= price",
            name=op.f("ck_product_variants_compare_at_price_gte_price"),
        ),
        sa.CheckConstraint("price >= 0", name=op.f("ck_product_variants_price_non_negative")),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_product_variants_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_variants")),
        sa.UniqueConstraint("product_id", "weight", name="uq_product_variants_product_id_weight"),
        sa.UniqueConstraint("sku", name=op.f("uq_product_variants_sku")),
    )
    op.create_index(
        op.f("ix_product_variants_product_id"), "product_variants", ["product_id"], unique=False
    )
    op.create_table(
        "reviews",
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_reviews_rating_range")),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_reviews_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    op.create_index(
        "ix_reviews_product_id_is_approved", "reviews", ["product_id", "is_approved"], unique=False
    )
    op.create_table(
        "shipments",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=40), server_default="manual", nullable=False),
        sa.Column("carrier", sa.String(length=80), nullable=True),
        sa.Column("tracking_number", sa.String(length=120), nullable=True),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "shipped",
                "out_for_delivery",
                "delivered",
                "returned",
                name="shipment_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_shipments_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipments")),
    )
    op.create_index(op.f("ix_shipments_order_id"), "shipments", ["order_id"], unique=False)
    op.create_index(
        "ix_shipments_provider_provider_reference",
        "shipments",
        ["provider", "provider_reference"],
        unique=False,
    )
    op.create_table(
        "inventory",
        sa.Column("variant_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), server_default="5", nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "low_stock_threshold >= 0", name=op.f("ck_inventory_low_stock_threshold_non_negative")
        ),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_inventory_quantity_non_negative")),
        sa.CheckConstraint(
            "reserved >= 0 AND reserved <= quantity",
            name=op.f("ck_inventory_reserved_within_quantity"),
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name=op.f("fk_inventory_variant_id_product_variants"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory")),
        sa.UniqueConstraint("variant_id", name=op.f("uq_inventory_variant_id")),
    )
    op.create_table(
        "order_items",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("variant_id", sa.UUID(), nullable=True),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("product_name_te", sa.String(length=200), nullable=True),
        sa.Column(
            "weight",
            sa.Enum(
                "250g",
                "500g",
                "1kg",
                name="order_item_weight",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_order_items_quantity_positive")),
        sa.CheckConstraint("unit_price >= 0", name=op.f("ck_order_items_unit_price_non_negative")),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_items_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_order_items_product_id_products"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name=op.f("fk_order_items_variant_id_product_variants"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_items")),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_order_items_variant_id"), "order_items", ["variant_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_order_items_variant_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_table("inventory")
    op.drop_index("ix_shipments_provider_provider_reference", table_name="shipments")
    op.drop_index(op.f("ix_shipments_order_id"), table_name="shipments")
    op.drop_table("shipments")
    op.drop_index("ix_reviews_product_id_is_approved", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index(op.f("ix_product_variants_product_id"), table_name="product_variants")
    op.drop_table("product_variants")
    op.drop_index(
        "uq_product_images_primary",
        table_name="product_images",
        postgresql_where=sa.text("is_primary"),
    )
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_table("product_images")
    op.drop_index("ix_payments_provider_provider_reference", table_name="payments")
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_order_status_history_order_id"), table_name="order_status_history")
    op.drop_table("order_status_history")
    op.drop_index(
        "uq_combo_offer_items_combo_product",
        table_name="combo_offer_items",
        postgresql_where=sa.text("product_id IS NOT NULL"),
    )
    op.drop_index(
        "uq_combo_offer_items_combo_category",
        table_name="combo_offer_items",
        postgresql_where=sa.text("category_id IS NOT NULL"),
    )
    op.drop_index(op.f("ix_combo_offer_items_product_id"), table_name="combo_offer_items")
    op.drop_index(op.f("ix_combo_offer_items_combo_id"), table_name="combo_offer_items")
    op.drop_index(op.f("ix_combo_offer_items_category_id"), table_name="combo_offer_items")
    op.drop_table("combo_offer_items")
    op.drop_index(
        "ix_products_name_trgm",
        table_name="products",
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.drop_index("ix_products_category_id_status", table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_orders_ship_mobile"), table_name="orders")
    op.drop_index("ix_orders_payment_status", table_name="orders")
    op.drop_index("ix_orders_order_status_created_at", table_name="orders")
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_coupon_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_addresses_customer_id"), table_name="addresses")
    op.drop_table("addresses")
    op.drop_table("website_settings")
    op.drop_table("customers")
    op.drop_table("coupons")
    op.drop_table("combo_offers")
    op.drop_table("categories")
    op.drop_index("ix_banners_is_active_sort_order", table_name="banners")
    op.drop_table("banners")
    op.drop_table("admins")
