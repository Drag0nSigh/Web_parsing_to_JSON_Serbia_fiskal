"""
Модели Pydantic для валидации и сериализации фискальных данных
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum



class PaymentType(str, Enum):
    """Типы оплаты"""
    CASH = "cash"
    CARD = "card"
    ELECTRONIC = "electronic"
    CREDIT = "credit"
    PREPAID = "prepaid"
    PROVISION = "provision"


class OperationType(int, Enum):
    """Типы операций"""
    SALE = 1
    RETURN = 2
    ADVANCE = 3
    CREDIT = 4


class TaxationType(int, Enum):
    """Типы налогообложения"""
    OSN = 1  # Общая система налогообложения
    USN_INCOME = 2  # УСН доходы
    USN_INCOME_EXPENSE = 3  # УСН доходы минус расходы
    ENVD = 4  # ЕНВД
    ESN = 5  # ЕСН
    PATENT = 6  # Патент


class ProductType(int, Enum):
    """Типы товаров"""
    PRODUCT = 1
    SERVICE = 2
    WORK = 3
    GAMBLING_BET = 4
    GAMBLING_WIN = 5
    LOTTERY_TICKET = 6
    LOTTERY_WIN = 7
    RID = 8
    PAYMENT = 9
    AGENT_COMMISSION = 10
    COMPOSITE = 11
    ANOTHER = 12


class NDSType(int, Enum):
    """Типы НДС"""
    NO_NDS = 0
    NDS_0 = 1
    NDS_10 = 2
    NDS_20 = 3
    NDS_10_110 = 4
    NDS_20_120 = 5


class Item(BaseModel):
    """Товар/услуга в чеке"""
    name: str = Field(..., description="Наименование товара/услуги")
    quantity: int = Field(..., description="Количество")
    price: int = Field(..., description="Цена за единицу")
    sum: int = Field(..., description="Сумма")
    nds: int = Field(..., description="Тип НДС")
    paymentType: int = Field(..., description="Тип оплаты")
    productType: int = Field(..., description="Тип товара")
    
    @model_validator(mode='after')
    def validate_sum(self):
        """Проверка соответствия суммы количеству и цене"""
        expected_sum = self.quantity * self.price
        if abs(self.sum - expected_sum) > 5:  # Допуск 5 копеек для округления
            raise ValueError(f"Сумма {self.sum} не соответствует количеству {self.quantity} * цена {self.price}")
        return self


class AmountsNds(BaseModel):
    """Суммы по типам НДС"""
    nds: int = Field(..., description="Тип НДС")
    ndsSum: int = Field(..., description="Сумма НДС")


class AmountsReceiptNds(BaseModel):
    """Суммы НДС по чеку"""
    amountsNds: List[AmountsNds] = Field(..., description="Список сумм по типам НДС")


class Receipt(BaseModel):
    """Фискальный чек"""
    # Порядок полей как в rus.json
    cashTotalSum: int = Field(default=0, description="Сумма наличными")
    code: int = Field(..., description="Код документа")
    creditSum: int = Field(default=0, description="Сумма кредитом")
    dateTime: str = Field(..., description="Дата и время операции")
    ecashTotalSum: int = Field(default=0, description="Сумма безналичными")
    fiscalDocumentFormatVer: int = Field(default=4, description="Версия формата фискального документа")
    fiscalDocumentNumber: int = Field(..., description="Номер фискального документа")
    fiscalDriveNumber: str = Field(..., description="Номер фискального накопителя")
    fiscalSign: int = Field(..., description="Фискальный признак")
    fnsUrl: str = Field(..., description="URL ФНС")
    items: List[Item] = Field(..., description="Список товаров/услуг")
    kktRegId: str = Field(..., description="Регистрационный номер ККТ")
    nds0: int = Field(default=0, description="Сумма НДС 0%")
    amountsReceiptNds: Optional[AmountsReceiptNds] = Field(None, description="Суммы НДС")
    operationType: int = Field(..., description="Тип операции")
    operator: Optional[str] = Field(None, description="Оператор")
    prepaidSum: int = Field(default=0, description="Сумма предоплатой")
    provisionSum: int = Field(default=0, description="Сумма встречным предоставлением")
    requestNumber: Optional[int] = Field(None, description="Номер запроса")
    retailPlace: str = Field(..., description="Место расчетов")
    retailPlaceAddress: str = Field(..., description="Адрес места расчетов")
    shiftNumber: Optional[int] = Field(None, description="Номер смены")
    taxationType: int = Field(..., description="Тип налогообложения")
    appliedTaxationType: int = Field(..., description="Применяемый тип налогообложения")
    totalSum: int = Field(..., description="Общая сумма чека")
    user: str = Field(..., description="Наименование организации")
    userInn: str = Field(..., description="ИНН организации")
    
    @model_validator(mode='after')
    def validate_total_sum(self):
        """Проверка соответствия общей суммы сумме товаров"""
        items_sum = sum(item.sum for item in self.items)
        if abs(self.totalSum - items_sum) > 5:  # Допуск 5 копеек для округления
            raise ValueError(f"Общая сумма {self.totalSum} не соответствует сумме товаров {items_sum}")
        return self


class Document(BaseModel):
    """Документ"""
    receipt: Receipt = Field(..., description="Фискальный чек")


class Ticket(BaseModel):
    """Билет/документ"""
    document: Document = Field(..., description="Документ")


class FiscalData(BaseModel):
    """Основная модель фискальных данных"""
    id: Optional[str] = Field(None, alias="_id", description="Идентификатор")
    created_at: Optional[str] = Field(None, alias="createdAt", description="Дата создания")
    ticket: Ticket = Field(..., description="Билет с фискальными данными")
    
    model_config = ConfigDict(
        json_schema_serialization_defaults_required=True
    )


# Модели для сербских фискальных данных
class SerbianFiscalData(BaseModel):
    """Модель для сербских фискальных данных (исходные данные из HTML)"""
    
    # Информация о продавце
    tin: str = Field(..., description="ПИБ (налоговый номер)")
    shop_name: str = Field(..., description="Название магазина")
    shop_address: str = Field(..., description="Адрес магазина")
    city: str = Field(..., description="Город")
    administrative_unit: str = Field(..., description="Општина")
    
    # Информация о чеке
    invoice_number: str = Field(..., description="Номер чека")
    total_amount: Decimal = Field(..., description="Общая сумма")
    transaction_type_counter: int = Field(..., description="Счетчик по типу транзакции")
    total_counter: int = Field(..., description="Общий счетчик")
    invoice_counter_extension: str = Field(..., description="Расширение счетчика чека")
    signed_by: str = Field(..., description="Подписан")
    sdc_date_time: datetime = Field(..., description="Время ПФР")
    
    # Дополнительная информация
    buyer_id: Optional[str] = Field(None, description="ID покупателя")
    requested_by: str = Field(..., description="Затребован")
    invoice_type: str = Field(..., description="Тип чека")
    transaction_type: str = Field(..., description="Тип транзакции")
    
    # Статус
    status: str = Field(..., description="Статус чека")
    
    # Товары
    items: List[Dict] = Field(default_factory=list, description="Список товаров")
    
    model_config = ConfigDict(
        json_schema_serialization_defaults_required=True,
        ser_json_datetime=lambda v: v.isoformat(),
        ser_json_decimal=lambda v: float(v)
    )
