"""
Working tests for actual project models
"""
import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from models.fiscal_models import (
    Item,
    SerbianFiscalData,
    FiscalData
)


class TestItemWorking:
    """Tests for Item model - working version."""
    
    def test_valid_item_creation(self):
        """Test creating valid item."""
        item = Item(
            name="Test Item",
            quantity=2,
            price=10000,  # 100.00 in kopecks
            sum=20000,    # 200.00 in kopecks
            nds=2,
            paymentType=4,
            productType=1
        )
        assert item.name == "Test Item"
        assert item.quantity == 2
        assert item.price == 10000
        assert item.sum == 20000
    
    def test_item_sum_validation_passes(self):
        """Test sum validation passes with correct values."""
        item = Item(
            name="Valid Item",
            quantity=3,
            price=5000,
            sum=15000,  # 3 * 5000 = 15000
            nds=2,
            paymentType=4,
            productType=1
        )
        assert item.sum == 15000
    
    def test_item_sum_validation_fails(self):
        """Test sum validation fails with incorrect values."""
        with pytest.raises(ValidationError):
            Item(
                name="Invalid Item",
                quantity=2,
                price=10000,
                sum=50000,  # Wrong sum: should be 20000
                nds=2,
                paymentType=4,
                productType=1
            )


class TestSerbianFiscalDataWorking:
    """Tests for SerbianFiscalData model - working version."""
    
    def get_valid_serbian_data(self):
        """Helper method to get valid Serbian fiscal data."""
        return {
            # Информация о продавце
            "tin": "123456789",
            "shop_name": "Test Shop",
            "shop_address": "Test Address 123",
            "city": "Belgrade",
            "administrative_unit": "Novi Beograd",
            
            # Информация о чеке
            "invoice_number": "ABCD-123-456",
            "total_amount": Decimal("183.96"),
            "transaction_type_counter": 456,
            "total_counter": 123,
            "invoice_counter_extension": "EXT-001",
            "signed_by": "System",
            "sdc_date_time": datetime(2025, 9, 27, 10, 30, 0),
            
            # Дополнительная информация  
            "requested_by": "Customer",
            "invoice_type": "NORMAL",
            "transaction_type": "SALE",
            
            # Статус
            "status": "COMPLETED",
            
            # Товары
            "items": [
                {
                    "name": "Test Item",
                    "quantity": Decimal("1"),
                    "price": Decimal("183.96"),
                    "sum": Decimal("183.96")
                }
            ]
        }
    
    def test_valid_serbian_data_creation(self):
        """Test creating valid Serbian fiscal data."""
        data = SerbianFiscalData(**self.get_valid_serbian_data())
        
        assert data.tin == "123456789"
        assert data.shop_name == "Test Shop"
        assert data.total_amount == Decimal("183.96")
        assert len(data.items) == 1
        assert data.status == "COMPLETED"
    
    def test_serbian_data_with_optional_buyer_id(self):
        """Test Serbian data with optional buyer_id."""
        data_dict = self.get_valid_serbian_data()
        data_dict["buyer_id"] = "BUYER123"
        
        data = SerbianFiscalData(**data_dict)
        assert data.buyer_id == "BUYER123"
    
    def test_serbian_data_with_multiple_items(self):
        """Test Serbian data with multiple items."""
        data_dict = self.get_valid_serbian_data()
        data_dict["items"] = [
            {
                "name": "Item 1",
                "quantity": Decimal("2"),
                "price": Decimal("50.00"),
                "sum": Decimal("100.00")
            },
            {
                "name": "Item 2",
                "quantity": Decimal("1"),
                "price": Decimal("83.96"),
                "sum": Decimal("83.96")
            }
        ]
        data_dict["total_amount"] = Decimal("183.96")
        
        data = SerbianFiscalData(**data_dict)
        assert len(data.items) == 2
        assert data.items[0]["name"] == "Item 1"
        assert data.items[1]["name"] == "Item 2"
    
    def test_serbian_data_missing_required_field(self):
        """Test Serbian data validation with missing required field."""
        data_dict = self.get_valid_serbian_data()
        del data_dict["tin"]  # Remove required field
        
        with pytest.raises(ValidationError):
            SerbianFiscalData(**data_dict)
    
    def test_serbian_data_with_special_characters(self):
        """Test Serbian data with special characters."""
        data_dict = self.get_valid_serbian_data()
        data_dict.update({
            "shop_name": "Тест Шоп ćčŽšđ",
            "shop_address": "Адреса тест ćčŽšđ 123", 
            "city": "Београд",
            "items": [
                {
                    "name": "Производ ćčŽšđ",
                    "quantity": Decimal("1"),
                    "price": Decimal("100.00"),
                    "sum": Decimal("100.00")
                }
            ]
        })
        data_dict["total_amount"] = Decimal("100.00")
        
        data = SerbianFiscalData(**data_dict)
        assert "ćčŽšđ" in data.shop_name
        assert "Београд" == data.city
        assert "ćčŽšđ" in data.items[0]["name"]


class TestModelValidationWorking:
    """Tests for model validation - working version."""
    
    def test_item_with_zero_values(self):
        """Test item with zero values."""
        item = Item(
            name="Free Item",
            quantity=1,
            price=0,
            sum=0,
            nds=0,
            paymentType=4,
            productType=1
        )
        assert item.price == 0
        assert item.sum == 0
    
    def test_large_amounts_in_item(self):
        """Test handling of large amounts in items."""
        large_amount = 999999999  # Large amount in kopecks
        
        item = Item(
            name="Expensive Item",
            quantity=1,
            price=large_amount,
            sum=large_amount,
            nds=2,
            paymentType=4,
            productType=1
        )
        assert item.price == large_amount
        assert item.sum == large_amount
    
    def test_item_sum_tolerance(self):
        """Test item sum validation tolerance."""
        # Should pass with small rounding difference (within 5 kopecks)
        item = Item(
            name="Tolerance Test",
            quantity=3,
            price=3333,  # 33.33 kopecks
            sum=10000,   # 100.00 kopecks (3333*3=9999, diff=1 kopeck)
            nds=2,
            paymentType=4,
            productType=1
        )
        assert item.sum == 10000
    
    def test_item_sum_exceeds_tolerance(self):
        """Test item sum validation fails when exceeding tolerance."""
        with pytest.raises(ValidationError):
            Item(
                name="Tolerance Fail",
                quantity=2,
                price=1000,   # 10.00
                sum=5000,     # 50.00 (should be 20.00, diff > 5 kopecks)
                nds=2,
                paymentType=4,
                productType=1
            )


class TestRealWorldScenarios:
    """Tests for real-world scenarios."""
    
    def test_typical_grocery_receipt(self):
        """Test typical grocery receipt scenario."""
        grocery_data = {
            "tin": "987654321",
            "shop_name": "Maxi Market",
            "shop_address": "Bulevar oslobođenja 123",
            "city": "Novi Sad",
            "administrative_unit": "Novi Sad",
            "invoice_number": "MAXI-001-789",
            "total_amount": Decimal("1247.50"),
            "transaction_type_counter": 1,
            "total_counter": 1001,
            "invoice_counter_extension": "NS-001",
            "signed_by": "POS System",
            "sdc_date_time": datetime(2025, 9, 27, 14, 25, 30),
            "requested_by": "Customer",
            "invoice_type": "RETAIL",
            "transaction_type": "SALE",
            "status": "COMPLETED",
            "items": [
                {
                    "name": "Hleb integralni 500g",
                    "quantity": Decimal("2"),
                    "price": Decimal("89.99"),
                    "sum": Decimal("179.98")
                },
                {
                    "name": "Mleko 2.8% 1L",
                    "quantity": Decimal("3"),
                    "price": Decimal("119.99"),
                    "sum": Decimal("359.97")
                },
                {
                    "name": "Jaja A klasa 10kom",
                    "quantity": Decimal("1"),
                    "price": Decimal("299.99"),
                    "sum": Decimal("299.99")
                },
                {
                    "name": "Banana 1kg",
                    "quantity": Decimal("1.245"),
                    "price": Decimal("329.99"),
                    "sum": Decimal("407.56")  # 1.245 * 329.99 ≈ 407.56
                }
            ]
        }
        
        data = SerbianFiscalData(**grocery_data)
        
        assert data.tin == "987654321"
        assert data.shop_name == "Maxi Market"
        assert len(data.items) == 4
        assert data.total_amount == Decimal("1247.50")
        assert "Novi Sad" in data.city
    
    def test_restaurant_receipt(self):
        """Test restaurant receipt scenario."""
        restaurant_data = {
            "tin": "111222333",
            "shop_name": "Restoran Tri Šešira", 
            "shop_address": "Skadarlija 29",
            "city": "Beograd",
            "administrative_unit": "Stari Grad",
            "invoice_number": "TRI-002-456",
            "total_amount": Decimal("3450.00"),
            "transaction_type_counter": 5,
            "total_counter": 2050,
            "invoice_counter_extension": "SG-002",
            "signed_by": "Waiter System",
            "sdc_date_time": datetime(2025, 9, 27, 19, 45, 15),
            "requested_by": "Table 7",
            "invoice_type": "RESTAURANT",
            "transaction_type": "SALE",
            "status": "COMPLETED",
            "buyer_id": "VIP123",
            "items": [
                {
                    "name": "Ćevapi 10kom sa lepinjom",
                    "quantity": Decimal("2"),
                    "price": Decimal("890.00"),
                    "sum": Decimal("1780.00")
                },
                {
                    "name": "Shopska salata",
                    "quantity": Decimal("1"),
                    "price": Decimal("450.00"),
                    "sum": Decimal("450.00")
                },
                {
                    "name": "Pivo Jelen 0.5L",
                    "quantity": Decimal("4"),
                    "price": Decimal("280.00"),
                    "sum": Decimal("1120.00")
                },
                {
                    "name": "Espresso kafa",
                    "quantity": Decimal("2"),
                    "price": Decimal("150.00"),
                    "sum": Decimal("300.00")
                }
            ]
        }
        
        data = SerbianFiscalData(**restaurant_data)
        
        assert data.shop_name == "Restoran Tri Šešira"
        assert data.buyer_id == "VIP123"
        assert len(data.items) == 4
        assert data.invoice_type == "RESTAURANT"
        assert "Ćevapi" in data.items[0]["name"]
