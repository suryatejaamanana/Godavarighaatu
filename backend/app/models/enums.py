import enum


class ProductStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Weight(enum.StrEnum):
    G250 = "250g"
    G500 = "500g"
    KG1 = "1kg"


class AdminRole(enum.StrEnum):
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    STAFF = "staff"


class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class ShipmentStatus(enum.StrEnum):
    PENDING = "pending"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RETURNED = "returned"


class DiscountType(enum.StrEnum):
    PERCENT = "percent"
    FIXED = "fixed"


class ComboRuleType(enum.StrEnum):
    FIXED_PRODUCTS = "fixed_products"
    ANY_N = "any_n"
