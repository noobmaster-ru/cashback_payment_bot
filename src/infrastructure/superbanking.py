import uuid
import logging 
import requests
from src.core.config import settings, constants
from src.tools.string_converter import StringConverter
from typing import Optional, Dict, Tuple

from src.core.config import constants

logger = logging.getLogger(__name__)


class Superbanking:
    def __init__(self):
        self.api_key = settings.SUPERBANKING_API_KEY
        self.cabinet_id = settings.SUPERBANKING_CABINET_ID
        self.project_id = settings.SUPERBANKING_PROJECT_ID
        self.clearing_center_id = settings.SUPERBANKING_CLEARING_CENTER_ID
        self.pay_number = 334
        self.ALIAS_MAP: Dict[str, str] = {}
        self.BANK_IDENTIFIERS: Dict[str, str] = {}
        self.order_number = None
        
    def post_api_balance(self) -> Tuple[int]:
        headers = {
            "x-token-user-api": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "cabinetId": self.cabinet_id,
            "projectId": self.project_id,
            "clearingCenterId": self.clearing_center_id
        } 
        try:
            response = requests.post(constants.url_api_balance, json=payload, headers=headers)
            response.raise_for_status()            
            resp_json = response.json()
            balance = resp_json["data"]["balance"]
            logger.info(f"balance = {balance}₽")
            return balance
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error, balance: %s", http_err)
            logger.error("body error, balance: %s", response.text)
            return -1
        except Exception as err:
            logger.error("error, balance: %s", err)   
            return -1
    
    # Дополнительные короткие АЛИАСЫ, которыми обычно пишут пользователи.
    # Здесь мы биндим алиас → identifier, используя SUPERBANKING_BANKS.
    def _find_by_rus_contains(self, substr: str) -> Optional[str]:
        subs_norm = StringConverter._norm(substr)
        for b in constants.SUPERBANKING_BANKS:
            if subs_norm in StringConverter._norm(b["nameRus"]):
                return b["identifier"]
        return None


    def _find_by_eng_contains(self, substr: str) -> Optional[str]:
        subs_norm = StringConverter._norm(substr)
        for b in constants.SUPERBANKING_BANKS:
            if subs_norm in StringConverter._norm(b["bankName"]):
                return b["identifier"]
        return None
    
    def _add_alias(self, alias: str, *, by_rus: Optional[str] = None, by_eng: Optional[str] = None):
        """
        alias – то, что пишет юзер ('сбер', 'тинькофф', 'т банк', 'ozon', 'wb').
        by_rus/by_eng – кусок официального названия, по которому ищем банк.
        """
        identifier = None
        if by_rus:
            identifier = Superbanking._find_by_rus_contains(self, by_rus)
        if identifier is None and by_eng:
            identifier = Superbanking._find_by_eng_contains(self, by_eng)

        if identifier:
            self.ALIAS_MAP[StringConverter._norm(alias)] = identifier
      
    def create_banks_ids(self):
        for b in constants.SUPERBANKING_BANKS:
            eng = StringConverter._norm(b["bankName"])
            rus = StringConverter._norm(b["nameRus"])
            if eng:
                self.BANK_IDENTIFIERS[eng] = b["identifier"]
            if rus:
                self.BANK_IDENTIFIERS[rus] = b["identifier"]
        # самые популярные варианты, ты можешь дополнять список
        Superbanking._add_alias(self, alias="сбер", by_rus="Сбербанк")
        Superbanking._add_alias(self, alias="сбербанк", by_rus="Сбербанк")
        Superbanking._add_alias(self, alias="сбер банк", by_rus="Сбербанк")
        Superbanking._add_alias(self, alias="сбер-банк", by_rus="Сбербанк")

        Superbanking._add_alias(self, alias="тиньков", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="тиньк", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="т банк", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="тбанк", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="т-банк", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="т- банк", by_eng="TINKOFF")
        Superbanking._add_alias(self, alias="т -банк", by_eng="TINKOFF")
        
        Superbanking._add_alias(self, alias="Альфа", by_rus="Альфа Банк")
        Superbanking._add_alias(self, alias="Альфабанк", by_rus="Альфа Банк")
        Superbanking._add_alias(self, alias="Альфа-банк", by_rus="Альфа Банк")

        Superbanking._add_alias(self, alias="Втб", by_rus="ВТБ")

        Superbanking._add_alias(self, alias="Озон", by_eng="OZON")
        Superbanking._add_alias(self, alias="ozon", by_eng="OZON")

        Superbanking._add_alias(self, alias="Райфайзен", by_rus="Райффайзенбанк")
        Superbanking._add_alias(self, alias="Райф", by_rus="Райффайзенбанк")
        Superbanking._add_alias(self, alias="Райфф", by_rus="Райффайзенбанк")
        Superbanking._add_alias(self, alias="Райффайзен", by_rus="Райффайзенбанк")

        Superbanking._add_alias(self, alias="росбанк", by_rus="Росбанк")
        Superbanking._add_alias(self, alias="открытие", by_rus="Открытие")
        Superbanking._add_alias(self, alias="почтабанк", by_rus="Почта Банк")
        Superbanking._add_alias(self, alias="почта банк", by_rus="Почта Банк")
        Superbanking._add_alias(self, alias="почта банк", by_rus="Почта Банк")
        Superbanking._add_alias(self, alias="совкомбанк", by_rus="Совкомбанк")
        Superbanking._add_alias(self, alias="мтс банк", by_rus="МТС-Банк")
        Superbanking._add_alias(self, alias="мтсбанк", by_rus="МТС-Банк")
        Superbanking._add_alias(self, alias="мтс-банк", by_rus="МТС-Банк")
        Superbanking._add_alias(self, alias="мтс", by_rus="МТС-Банк")

        Superbanking._add_alias(self, alias="яндекс", by_eng="YANDEX BANK")
        Superbanking._add_alias(self, alias="яндексбанк", by_eng="YANDEX BANK")
        Superbanking._add_alias(self, alias="yandex", by_eng="YANDEX BANK")

        Superbanking._add_alias(self, alias="юмани", by_rus="ЮМани")
        Superbanking._add_alias(self, alias="юmoney", by_eng="YOOMONEY")

        Superbanking._add_alias(self, alias="вббанк", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="вб банк", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="вб-банк", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="wbбанк", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="wildberries", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="вб", by_eng="Wildberries Bank")
        Superbanking._add_alias(self, alias="wb", by_eng="Wildberries Bank")

        Superbanking._add_alias(self, alias="газпромбанк", by_eng="Газпромбанк")
        Superbanking._add_alias(self, alias="газпром", by_eng="Газпромбанк")
        Superbanking._add_alias(self, alias="газпром банк", by_eng="Газпромбанк")
        Superbanking._add_alias(self, alias="газпром Банк", by_eng="Газпромбанк")
        
        Superbanking._add_alias(self, alias="толчка", by_eng="TOCHKA BANK")  # если будут писать странно – добавишь свои варианты
        Superbanking._add_alias(self, alias="точка", by_eng="TOCHKA BANK")
        
        Superbanking._add_alias(self, alias="псб", by_eng="Промсвязьбанк")

    def parse_bank_identifier(self, text: str) -> Optional[str]:
        """
        Пытается определить identifier банка по произвольному тексту пользователя.

        Логика:
        1) Смотрим на алиасы (сбер, тинькофф, озон, ...).
        2) Если не сработало – пробегаемся по всему списку банков и ищем
            вхождение полного русского/английского названия в тексте.
        """
        t = StringConverter._norm(text)

        # 1. Алиасы
        for alias_norm, identifier in self.ALIAS_MAP.items():
            if alias_norm in t:
                return identifier

        # 2. Полные названия (по списку)
        for b in constants.SUPERBANKING_BANKS:
            if StringConverter._norm(b["nameRus"]) in t or StringConverter._norm(b["bankName"]) in t:
                return b["identifier"]

        return None
    
    def post_create_and_sign_payment(
        self,
        phone: str,
        bank_identifier: str,  
        amount: int
    ) -> Tuple[int, str]:
        uid_token = str(uuid.uuid4())
        headers = {
            "x-token-user-api": self.api_key,
            "x-idempotency-token": uid_token, # Генерация уникального ключа идемпотентности
            "Content-Type": "application/json"
        }
        order_number =f"{constants.order_number_hash}-{self.pay_number}"
        self.order_number = order_number
        payload = {
            "cabinetId": self.cabinet_id,
            "projectId": self.project_id,
            "orderNumber": order_number, 
            "phone": phone, # "0079876543210"
            "bank": bank_identifier, # "SBER" = 100000000111 , "TINKOFF" = 100000000004
            "amount": amount, 
            "purposePayment": "выплата кэшбека",
            "comment": "выплата кэшбека"
        }
        self.pay_number += 1
        try:
            response = requests.post(constants.url_create, json=payload, headers=headers)
            response.raise_for_status()            
            resp_json = response.json()
            payment_id = resp_json["data"]["payout"]["id"]
            headers = {
                "x-token-user-api": self.api_key,
                "x-idempotency-token": uid_token, # Генерация уникального ключа идемпотентности
                "Content-Type": "application/json"
            }
            payload = {
                "cabinetId": self.cabinet_id,
                "cabinetTransactionId": payment_id,
            }
            try:
                response = requests.post(constants.url_sign, json=payload, headers=headers)
                response.raise_for_status()
                return response.status_code, order_number
            except requests.exceptions.HTTPError as http_err:
                logger.error("HTTP error, sign: %s", http_err)
                logger.error("error.text, sign: %s", response.text)
            except Exception as err:
                logger.error("Произошла ошибка, sign: %s", err)
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error, create: %s", http_err)
            logger.error("error.text, create: %s", response.text)
        except Exception as err:
            logger.error(err)   
        return response.status_code, order_number

    def post_confirm_operation(self, order_number: str):
        headers = {
            "x-token-user-api": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "cabinetId": self.cabinet_id,
            "orderNumber": order_number, # EsLabCashBot
        }
        try:
            response = requests.post(constants.url_confirm_operation, json=payload, headers=headers)
            response.raise_for_status()            
            resp_json = response.json()
            check_photo_url = resp_json["data"]["url"]
            return response.status_code, check_photo_url
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error, confirm_payment: %s", http_err)
            logger.error("error.text, confirm_payment: %s", response.text)
        except Exception as err:
            logger.error(err)   
        return response.status_code, "none"