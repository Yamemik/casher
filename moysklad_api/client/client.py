import typing
import base64
import datetime
import json

import aiohttp
import asyncio
import aiohttp.client_exceptions

from ..errors import MoySkladError
from .. import types
from ..types import Unset

from ..api.entities import (
    product as product_api,
    product_folder as product_folder_api,
    custom_entity as custom_entity_api,
    organization as organization_api,
    webhook as webhook_api,
)
from ..api.reports import (
    stock as stock_api,
)
from ..api.documents import (
    internal_order as order_api,
)


class MoySkladClient:
    def __init__(
        self,
        login: typing.Union[Unset, str] = Unset,
        password: typing.Union[Unset, str] = Unset,
        api_token: typing.Union[Unset, str] = Unset,
        debug: bool = False,
        auto_retry_count: int = 5,
        auto_retry_delay: float = 1.0,
    ):
        """
        Create a MoySkladClient instance. Converts login and password to api_token, if needed.
        Either login and password or api_token must be provided.
        (Создает экземпляр MoySkladClient. Конвертирует логин и пароль в api_token, если нужно.
        Либо логин и пароль, либо api_token должны быть указаны.)

        :param login: Optional login (Логин)
        :param password:  Optional password (Пароль)
        :param api_token:  Optional api_token (Токен)
        :param debug:  If True, prints all requests and responses (Если True, печатает все запросы и ответы)
        :param auto_retry_count:  Number of times to retry a request if it fails (ClientConnectError, errorcode > 500, etc) (Количество попыток повторить запрос, если он не удался (ClientConnectError, errorcode> 500 и т. Д.))
        :param auto_retry_delay:  Delay between retries (Задержка между повторами)
        """
        if not (login and password) and not api_token:
            raise ValueError("Either login and password or api_token must be provided")
        if not api_token:
            api_token = base64.b64encode(f"{login}:{password}".encode()).decode()
        else:
            # check if api_token is valid base64 and has `:` in it
            # (проверяем, что api_token - это валидный base64 и содержит `:`)
            try:
                decoded = base64.b64decode(api_token).decode()
            except Exception:
                raise ValueError("api_token is not valid base64")
            if ":" not in decoded:
                raise ValueError("api_token is not valid, no : in it")

        self._api_token = api_token
        self._debug = debug
        self._auto_retry_count = auto_retry_count if auto_retry_count > 0 else 0
        if auto_retry_delay < 0:
            raise ValueError("auto_retry_delay must be >= 0")
        self._auto_retry_delay = auto_retry_delay

    async def request(
        self,
        method: typing.Literal["GET", "POST", "PUT", "DELETE"],
        url: str,
        allow_non_json=False,
        **kwargs,
    ) -> dict:
        """
        Make a request to the MoySklad API, automatically adding the Authorization header.
        (Делает запрос к API MoySklad, автоматически добавляя заголовок Authorization.)

        :raises MoySkladError: if the request failed (Сообщает об ошибке, если запрос не удался)

        :param method: HTTP method GET, POST, PUT, DELETE
        :param url:  URL to request (URL для запроса)
        :param allow_non_json:  If True, error is not raised if the response is not JSON (Если True, ошибка не вызывается, если ответ не JSON)
        :param kwargs:  Additional arguments for aiohttp.ClientSession.request
         (Дополнительные аргументы для aiohttp.ClientSession.request)

        :return: JSON Response from the MoySklad API (JSON Ответ от MoySklad API)
        """
        async with aiohttp.ClientSession() as session:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["Authorization"] = f"Basic {self._api_token}"
            is_json = kwargs.get("json") is not None
            json_text = "{}"
            if is_json:
                if self._debug:
                    # convert json to a body with a pretty printed json, set content-type to application/json.
                    # This is needed for better error reading.
                    # (конвертируем json в тело с красиво отформатированным json,
                    # устанавливаем content-type в application/json)
                    # (это нужно для лучшего чтения ошибок)
                    kwargs["data"] = json.dumps(
                        kwargs.pop("json", {}), indent=4, ensure_ascii=False
                    )
                else:
                    kwargs["data"] = json.dumps(
                        kwargs.pop("json", {}),
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                json_text = kwargs["data"]
                kwargs["headers"]["Content-Type"] = "application/json"

            # allow gzipped responses
            # (разрешаем сжатые ответы)
            kwargs["headers"]["Accept-Encoding"] = "gzip"

            last_exception = None
            for retry_num in range(1, self._auto_retry_count + 1):
                is_last_retry = retry_num == self._auto_retry_count
                try:
                    async with session.request(method, url, **kwargs) as resp:
                        if self._debug:
                            print(
                                f"Request: {method} {url} {kwargs.get('json', '')} {kwargs.get('data', '')}\n"
                                f"Response: {resp.status} {await resp.text()}"
                            )
                        if resp.status >= 500:
                            try:
                                json_resp = await resp.json()
                            except (aiohttp.ContentTypeError, json.JSONDecodeError):
                                json_resp = {}
                            last_exception = MoySkladError(
                                json_resp.get(
                                    "errors",
                                    {"error": f"Server returned {resp.status}"},
                                ),
                                json_text,
                            )
                            if is_last_retry:
                                raise last_exception
                            await asyncio.sleep(self._auto_retry_delay)
                            continue
                        if resp.content_type != "application/json":
                            if allow_non_json:
                                return {}
                            raise ValueError(
                                f"Response is not JSON: `{resp.content_type}` : {await resp.text()}"
                            )
                        json_resp = await resp.json()
                        if resp.status >= 400:
                            raise MoySkladError(json_resp["errors"][0], json_text)
                        return json_resp
                except (
                    aiohttp.client_exceptions.ClientConnectorError,
                    asyncio.TimeoutError,
                ) as e:
                    if is_last_retry:
                        raise e
                    await asyncio.sleep(self._auto_retry_delay)
                    last_exception = e
        if last_exception is not None:
            raise last_exception
        raise ValueError("This should never happen")

    async def raw_request(
        self,
        *args,
        **kwargs,
    ) -> (int, bytes, dict):
        """
        Make a request to the MoySklad API, automatically adding the Authorization header.
        (Делает запрос к API MoySklad, автоматически добавляя заголовок Authorization.)

        :returns (status, body, headers): status code, body and headers of the response
        """
        async with aiohttp.ClientSession() as session:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["Authorization"] = f"Basic {self._api_token}"
            kwargs["headers"]["Accept-Encoding"] = "gzip"

            async with session.request(*args, **kwargs) as resp:
                return resp.status, await resp.read(), resp.headers

    # function that allows us to use MoySkladClient as a caller
    # (функция, которая позволяет нам использовать MoySkladClient как вызывающий)
    async def __call__(self, request):
        if not isinstance(request, types.ApiRequest):
            raise TypeError("request must be an ApiRequest")
        result = await self.request(**request.to_request().to_kwargs())
        return request.from_response(result)

    # orders
    async def get_orders(
        self,
        limit: typing.Union[Unset, int] = Unset,
        offset: typing.Union[Unset, int] = Unset,
        search: typing.Union[Unset, str] = Unset,
    ) -> typing.List[order_api.InternalOrder]:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/documents/#dokumenty-vnutrennij-zakaz-poluchit-vnutrennie-zakazy

        Get a list of internal orders. (Получает список внутренних заказов.)
        :param limit: Limit the number of results (Ограничить количество результатов)
        :param offset:  Offset the results (Сместить результаты)
        :param search:  Search query (Поисковый запрос)
        :return: List of InternalOrder objects (Список объектов InternalOrder)
        """
        return await self(
            order_api.GetInternalOrdersRequest(
                limit=limit, offset=offset, search=search
            )
        )

    # products_api
    async def get_product_list(
        self,
        limit: typing.Union[Unset, int] = Unset,
        offset: typing.Union[Unset, int] = Unset,
    ) -> typing.List[product_api.Product]:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-poluchit-spisok-towarow

        Get a list of product. (Получает список товаров.)
        :param limit: Limit (Ограничение)
        :param offset: Offset (Смещение)
        :return: list(Product) object (Список объектов Product)
        """
        return await self(product_api.GetProductListRequest(limit=limit, offset=offset))

    async def create_product(
        self,
        name: str,
        code: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        vat: typing.Union[Unset, int] = Unset,
        effective_vat: typing.Union[Unset, int] = Unset,
        discount_prohibited: typing.Union[Unset, bool] = Unset,
        uom: typing.Union[Unset, types.Meta] = Unset,
        supplier: typing.Union[Unset, types.Meta] = Unset,
        min_price: typing.Union[Unset, dict] = Unset,
        buy_price: typing.Union[Unset, dict] = Unset,
        sale_prices: typing.Union[Unset, typing.List[dict]] = Unset,
        barcodes: typing.Union[Unset, typing.List[dict]] = Unset,
        article: typing.Union[Unset, str] = Unset,
        weight: typing.Union[Unset, int] = Unset,
        volume: typing.Union[Unset, int] = Unset,
        packs: typing.Union[Unset, typing.List[dict]] = Unset,
        is_serial_trackable: typing.Union[Unset, bool] = Unset,
        tracking_type: typing.Union[
            Unset,
            typing.Literal[
                "ELECTRONICS",
                "LP_CLOTHES",
                "LP_LINENS",
                "MILK",
                "NCP",
                "NOT_TRACKED",
                "OTP",
                "PERFUMERY",
                "SHOES",
                "TIRES",
                "TOBACCO",
                "WATER",
            ],
        ] = Unset,
        attributes: typing.Union[Unset, typing.List[dict]] = Unset,
        images: typing.Union[Unset, typing.List[dict]] = Unset,
        alcoholic: typing.Union[Unset, dict] = Unset,
        archived: typing.Union[Unset, bool] = Unset,
        country: typing.Union[Unset, types.Meta] = Unset,
        files: typing.Union[Unset, typing.List[dict]] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        minimum_balance: typing.Union[Unset, int] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        partial_disposal: typing.Union[Unset, bool] = Unset,
        payment_item_type: typing.Union[
            Unset,
            typing.Literal[
                "GOODS",
                "EXCISABLE_GOOD",
                "COMPOUND_PAYMENT_ITEM",
                "ANOTHER_PAYMENT_ITEM",
            ],
        ] = Unset,
        ppe_type: typing.Union[Unset, str] = Unset,
        product_folder: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
        tax_system: typing.Union[
            Unset,
            typing.Literal[
                "GENERAL_TAX_SYSTEM",
                "PATENT_BASED",
                "PRESUMPTIVE_TAX_SYSTEM",
                "SIMPLIFIED_TAX_SYSTEM_INCOME",
                "SIMPLIFIED_TAX_SYSTEM_INCOME_OUTCOME",
                "TAX_SYSTEM_SAME_AS_GROUP",
                "UNIFIED_AGRICULTURAL_TAX",
            ],
        ] = Unset,
        things: typing.Union[Unset, typing.List[str]] = Unset,
        tnved: typing.Union[Unset, str] = Unset,
        use_parent_vat: typing.Union[Unset, bool] = Unset,
    ) -> product_api.Product:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-sozdat-towar

        :param name: Name (Название)
        :param code: Code (Код Комплекта)
        :param external_code: External code (Внешний код комплекта)
        :param description: Description (Описание)
        :param vat: VAT (НДС)
        :param effective_vat: Real VAT (Реальный НДС)
        :param discount_prohibited: Prohibition of discounts (Запрет на скидки)
        :param uom: Unit (Единица измерения)
        :param supplier: Supplier (Поставщик)
        :param min_price: Minimum price (Минимальная цена) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-minimal-naq-cena
        :param buy_price: Purchase price (Закупочная цена) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-wlozhennyh-suschnostej-zakupochnaq-cena
        :param sale_prices: Sale prices (Цены продажи)
        :param barcodes: Barcodes (Штрихкоды) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-shtrih-kody
        :param article: Article (Артикул)
        :param weight: Weight (Вес)
        :param volume: Volume (Объем)
        :param packs: Packs (Упаковки модификации) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-upakowki-modifikacii
        :param is_serial_trackable: Serial tracking (Серийный учет)
        :param tracking_type: Tracking type (Тип отслеживания) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-tip-markiruemoj-produkcii
        :param attributes: Attributes (Атрибуты)
        :param images: Images (Изображения) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-izobrazhenie
        :param alcoholic: Alcoholic (Объект, содержащий поля алкогольной продукции) https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-wlozhennyh-suschnostej-ob-ekt-soderzhaschij-polq-alkogol-noj-produkcii
        :param archived: Archived (Архивный)
        :param country: Country (Страна)
        :param files: Files (Метаданные массива Файлов (Максимальное количество файлов - 100))
        :param group: Group (Метаданные отдела сотрудника)
        :param minimum_balance: Minimum balance (Минимальный остаток)
        :param owner: Owner (Метаданные владельца (Сотрудника))
        :param partial_disposal: Partial disposal (Управление состоянием частичного выбытия маркированного товара. «true» - возможность включена.)
        :param payment_item_type: Payment item type (Признак предмета расчета. https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-komplekt-komplekty-atributy-suschnosti-priznak-predmeta-rascheta)
        :param ppe_type: PPE type (Код вида номенклатурной классификации медицинских средств индивидуальной защиты (EAN-13)) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-kod-wida-nomenklaturnoj-klassifikacii-medicinskih-sredstw-indiwidual-noj-zaschity
        :param product_folder: Product folder (Метаданные группы товара)
        :param shared: Shared (Общий)
        :param tax_system: Tax system (Система налогообложения) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-kod-sistemy-nalogooblozheniq
        :param things: Serial numbers (Серийные номера)
        :param tnved: TNVED (Код ТН ВЭД)
        :param use_parent_vat: Use parent VAT (Использовать родительский НДС)
        :return: Product object (Объект Product)
        """
        return await self(
            product_api.CreateProductRequest(
                name=name,
                code=code,
                external_code=external_code,
                description=description,
                vat=vat,
                effective_vat=effective_vat,
                discount_prohibited=discount_prohibited,
                uom=uom,
                supplier=supplier,
                min_price=min_price,
                buy_price=buy_price,
                sale_prices=sale_prices,
                barcodes=barcodes,
                article=article,
                weight=weight,
                volume=volume,
                packs=packs,
                is_serial_trackable=is_serial_trackable,
                tracking_type=tracking_type,
                attributes=attributes,
                images=images,
                alcoholic=alcoholic,
                archived=archived,
                country=country,
                files=files,
                group=group,
                minimum_balance=minimum_balance,
                owner=owner,
                partial_disposal=partial_disposal,
                payment_item_type=payment_item_type,
                ppe_type=ppe_type,
                product_folder=product_folder,
                shared=shared,
                tax_system=tax_system,
                things=things,
                tnved=tnved,
                use_parent_vat=use_parent_vat,
            )
        )

    async def delete_product(self, id_: str) -> None:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-udalit-towar

        :param id_: Product ID (ID Товара)
        :return: None
        """
        await self(product_api.DeleteProductRequest(id_=id_))

    async def get_product(self, id_: str) -> product_api.Product:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-poluchit-towar

        :param id_: Product ID (ID Товара)
        :return: Product object (Объект Product)
        """
        return await self(product_api.GetProductRequest(id_=id_))

    async def update_product(
        self,
        id_: str,
        name: typing.Union[Unset, str] = Unset,
        code: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        vat: typing.Union[Unset, int] = Unset,
        effective_vat: typing.Union[Unset, int] = Unset,
        discount_prohibited: typing.Union[Unset, bool] = Unset,
        uom: typing.Union[Unset, types.Meta] = Unset,
        supplier: typing.Union[Unset, types.Meta] = Unset,
        min_price: typing.Union[Unset, dict] = Unset,
        buy_price: typing.Union[Unset, dict] = Unset,
        sale_prices: typing.Union[Unset, typing.List[dict]] = Unset,
        barcodes: typing.Union[Unset, typing.List[dict]] = Unset,
        article: typing.Union[Unset, str] = Unset,
        weight: typing.Union[Unset, int] = Unset,
        volume: typing.Union[Unset, int] = Unset,
        packs: typing.Union[Unset, typing.List[dict]] = Unset,
        is_serial_trackable: typing.Union[Unset, bool] = Unset,
        tracking_type: typing.Union[
            Unset,
            typing.Literal[
                "ELECTRONICS",
                "LP_CLOTHES",
                "LP_LINENS",
                "MILK",
                "NCP",
                "NOT_TRACKED",
                "OTP",
                "PERFUMERY",
                "SHOES",
                "TIRES",
                "TOBACCO",
                "WATER",
            ],
        ] = Unset,
        attributes: typing.Union[Unset, typing.List[dict]] = Unset,
        images: typing.Union[Unset, typing.List[dict]] = Unset,
        alcoholic: typing.Union[Unset, dict] = Unset,
        archived: typing.Union[Unset, bool] = Unset,
        country: typing.Union[Unset, types.Meta] = Unset,
        files: typing.Union[Unset, typing.List[dict]] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        minimum_balance: typing.Union[Unset, int] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        partial_disposal: typing.Union[Unset, bool] = Unset,
        payment_item_type: typing.Union[
            Unset,
            typing.Literal[
                "GOODS",
                "EXCISABLE_GOOD",
                "COMPOUND_PAYMENT_ITEM",
                "ANOTHER_PAYMENT_ITEM",
            ],
        ] = Unset,
        ppe_type: typing.Union[Unset, str] = Unset,
        product_folder: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
        tax_system: typing.Union[
            Unset,
            typing.Literal[
                "GENERAL_TAX_SYSTEM",
                "PATENT_BASED",
                "PRESUMPTIVE_TAX_SYSTEM",
                "SIMPLIFIED_TAX_SYSTEM_INCOME",
                "SIMPLIFIED_TAX_SYSTEM_INCOME_OUTCOME",
                "TAX_SYSTEM_SAME_AS_GROUP",
                "UNIFIED_AGRICULTURAL_TAX",
            ],
        ] = Unset,
        things: typing.Union[Unset, typing.List[str]] = Unset,
        tnved: typing.Union[Unset, str] = Unset,
        use_parent_vat: typing.Union[Unset, bool] = Unset,
    ) -> product_api.Product:
        """
        https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-izmenit-towar

        :param id_: Product ID (ID Товара)
        :param name: Name (Название)
        :param code: Code (Код Комплекта)
        :param external_code: External code (Внешний код комплекта)
        :param description: Description (Описание)
        :param vat: VAT (НДС)
        :param effective_vat: Real VAT (Реальный НДС)
        :param discount_prohibited: Prohibition of discounts (Запрет на скидки)
        :param uom: Unit (Единица измерения)
        :param supplier: Supplier (Поставщик)
        :param min_price: Minimum price (Минимальная цена) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-minimal-naq-cena
        :param buy_price: Purchase price (Закупочная цена) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-wlozhennyh-suschnostej-zakupochnaq-cena
        :param sale_prices: Sale prices (Цены продажи)
        :param barcodes: Barcodes (Штрихкоды) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-shtrih-kody
        :param article: Article (Артикул)
        :param weight: Weight (Вес)
        :param volume: Volume (Объем)
        :param packs: Packs (Упаковки модификации) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-modifikaciq-modifikacii-atributy-wlozhennyh-suschnostej-upakowki-modifikacii
        :param is_serial_trackable: Serial tracking (Серийный учет)
        :param tracking_type: Tracking type (Тип отслеживания) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-tip-markiruemoj-produkcii
        :param attributes: Attributes (Атрибуты)
        :param images: Images (Изображения) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-izobrazhenie
        :param alcoholic: Alcoholic (Объект, содержащий поля алкогольной продукции) https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-wlozhennyh-suschnostej-ob-ekt-soderzhaschij-polq-alkogol-noj-produkcii
        :param archived: Archived (Архивный)
        :param country: Country (Страна)
        :param files: Files (Метаданные массива Файлов (Максимальное количество файлов - 100))
        :param group: Group (Метаданные отдела сотрудника)
        :param minimum_balance: Minimum balance (Минимальный остаток)
        :param owner: Owner (Метаданные владельца (Сотрудника))
        :param partial_disposal: Partial disposal (Управление состоянием частичного выбытия маркированного товара. «true» - возможность включена.)
        :param payment_item_type: Payment item type (Признак предмета расчета. https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-komplekt-komplekty-atributy-suschnosti-priznak-predmeta-rascheta)
        :param ppe_type: PPE type (Код вида номенклатурной классификации медицинских средств индивидуальной защиты (EAN-13)) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-kod-wida-nomenklaturnoj-klassifikacii-medicinskih-sredstw-indiwidual-noj-zaschity
        :param product_folder: Product folder (Метаданные группы товара)
        :param shared: Shared (Общий)
        :param tax_system: Tax system (Система налогообложения) - https://dev.moysklad.ru/doc/api/remap/1.2/dictionaries/#suschnosti-towar-towary-atributy-suschnosti-kod-sistemy-nalogooblozheniq
        :param things: Serial numbers (Серийные номера)
        :param tnved: TNVED (Код ТН ВЭД)
        :param use_parent_vat: Use parent VAT (Использовать родительский НДС)
        :return: Product object (Объект Product)
        """

        return await self(
            product_api.UpdateProductRequest(
                id_=id_,
                name=name,
                code=code,
                external_code=external_code,
                description=description,
                vat=vat,
                effective_vat=effective_vat,
                discount_prohibited=discount_prohibited,
                uom=uom,
                supplier=supplier,
                min_price=min_price,
                buy_price=buy_price,
                sale_prices=sale_prices,
                barcodes=barcodes,
                article=article,
                weight=weight,
                volume=volume,
                packs=packs,
                is_serial_trackable=is_serial_trackable,
                tracking_type=tracking_type,
                attributes=attributes,
                images=images,
                alcoholic=alcoholic,
                archived=archived,
                country=country,
                files=files,
                group=group,
                minimum_balance=minimum_balance,
                owner=owner,
                partial_disposal=partial_disposal,
                payment_item_type=payment_item_type,
                ppe_type=ppe_type,
                product_folder=product_folder,
                shared=shared,
                tax_system=tax_system,
                things=things,
                tnved=tnved,
                use_parent_vat=use_parent_vat,
            )
        )

    # product folders
    async def get_product_folders(
        self, limit: int = 1000, offset: int = 0
    ) -> typing.List[product_folder_api.ProductFolder]:
        """
        Get product folders (Получить папки товаров)
        :param limit: Limit of entities to extract. Allowed values 1 - 1000. (Лимит сущностей для извлечения. Допустимые значения 1 - 1000.)
        :param offset: Offset in the list of entities returned. (Отступ в выдаваемом списке сущностей.)
        :return: List of product folders (Список папок товаров)
        """
        return await self(
            product_folder_api.GetProductFoldersRequest(limit=limit, offset=offset)
        )

    async def create_product_folder(
        self,
        name: str,
        code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        meta: typing.Union[Unset, types.Meta] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        product_folder: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
        tax_system: typing.Union[
            Unset,
            typing.Literal[
                "GENERAL_TAX_SYSTEM",
                "PATENT_BASED",
                "PRESUMPTIVE_TAX_SYSTEM",
                "SIMPLIFIED_TAX_SYSTEM_INCOME",
                "SIMPLIFIED_TAX_SYSTEM_INCOME_OUTCOME",
                "TAX_SYSTEM_SAME_AS_GROUP",
                "UNIFIED_AGRICULTURAL_TAX",
            ],
        ] = Unset,
        use_parent_vat: typing.Union[Unset, bool] = Unset,
        vat: typing.Union[Unset, int] = Unset,
        vat_enabled: typing.Union[Unset, bool] = Unset,
    ) -> product_folder_api.ProductFolder:
        """
        Create product folder (Создать папку товаров)

        :param name: Name of the product folder (Имя группы товаров)
        :param code: Code of the product folder (Код группы товаров)
        :param description: Description of the product folder (Описание группы товаров)
        :param external_code: External code of the product folder (Внешний код группы товаров)
        :param group: Group of the product folder (Группа группы товаров)
        :param meta: Meta of the product folder (Метаданные группы товаров)
        :param owner: Owner of the product folder (Владелец группы товаров)
        :param product_folder: Product folder of the product folder (Группа товаров группы товаров)
        :param shared: Shared of the product folder (Общий доступ группы товаров)
        :param tax_system: Tax system of the product folder (Код системы налогообложения группы товаров)
        :param use_parent_vat: Use parent vat of the product folder (Используется ли ставка НДС родительской группы)
        :param vat: Vat of the product folder (НДС % группы товаров)
        :param vat_enabled: Vat enabled of the product folder (Включен ли НДС для группы товаров)
        :return: Created product folder (Созданная группа товаров)
        """

        return await self(
            product_folder_api.CreateProductFolderRequest(
                name=name,
                code=code,
                description=description,
                external_code=external_code,
                group=group,
                meta=meta,
                owner=owner,
                product_folder=product_folder,
                shared=shared,
                tax_system=tax_system,
                use_parent_vat=use_parent_vat,
                vat=vat,
                vat_enabled=vat_enabled,
            )
        )

    async def delete_product_folder(
        self,
        folder_id: str,
    ):
        """
        Delete product folder (Удалить папку товаров)
        :param folder_id: Product folder id (ID папки товаров)
        :return: None
        """
        return await self(
            product_folder_api.DeleteProductFolderRequest(folder_id=folder_id)
        )

    async def get_product_folder(
        self,
        folder_id: str,
    ) -> product_folder_api.ProductFolder:
        """
        Get product folder by id (Получить папку товаров по ID)
        :param folder_id: Product folder id (ID папки товаров)
        :return: Product folder (Папка товаров)
        """
        return await self(
            product_folder_api.GetProductFolderRequest(folder_id=folder_id)
        )

    async def update_product_folder(
        self,
        folder_id: str,
        name: typing.Union[Unset, str] = Unset,
        code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        meta: typing.Union[Unset, types.Meta] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        product_folder: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
        tax_system: typing.Union[
            Unset,
            typing.Literal[
                "GENERAL_TAX_SYSTEM",
                "PATENT_BASED",
                "PRESUMPTIVE_TAX_SYSTEM",
                "SIMPLIFIED_TAX_SYSTEM_INCOME",
                "SIMPLIFIED_TAX_SYSTEM_INCOME_OUTCOME",
                "TAX_SYSTEM_SAME_AS_GROUP",
                "UNIFIED_AGRICULTURAL_TAX",
            ],
        ] = Unset,
        use_parent_vat: typing.Union[Unset, bool] = Unset,
        vat: typing.Union[Unset, int] = Unset,
        vat_enabled: typing.Union[Unset, bool] = Unset,
    ) -> product_folder_api.ProductFolder:
        """
        Update product folder (Обновить папку товаров)
        :param folder_id: Product folder id (ID папки товаров)
        :param name: Name of the product folder (Имя группы товаров)
        :param code: Code of the product folder (Код группы товаров)
        :param description: Description of the product folder (Описание группы товаров)
        :param external_code: External code of the product folder (Внешний код группы товаров)
        :param group: Group of the product folder (Группа группы товаров)
        :param meta: Meta of the product folder (Метаданные группы товаров)
        :param owner: Owner of the product folder (Владелец группы товаров)
        :param product_folder: Product folder of the product folder (Группа товаров группы товаров)
        :param shared: Shared of the product folder (Общий доступ группы товаров)
        :param tax_system: Tax system of the product folder (Код системы налогообложения группы товаров)
        :param use_parent_vat: Use parent vat of the product folder (Используется ли ставка НДС родительской группы)
        :param vat: Vat of the product folder (НДС % группы товаров)
        :param vat_enabled: Vat enabled of the product folder (Включен ли НДС для группы товаров)
        :return: Updated product folder (Обновленная группа товаров)
        """
        return await self(
            product_folder_api.UpdateProductFolderRequest(
                folder_id=folder_id,
                name=name,
                code=code,
                description=description,
                external_code=external_code,
                group=group,
                meta=meta,
                owner=owner,
                product_folder=product_folder,
                shared=shared,
                tax_system=tax_system,
                use_parent_vat=use_parent_vat,
                vat=vat,
                vat_enabled=vat_enabled,
            )
        )

    # stock
    async def get_full_stock_report(
        self,
        limit: typing.Union[Unset, int] = 1000,
        offset: typing.Union[Unset, int] = 0,
        group_by: typing.Union[
            Unset, typing.Literal["product", "variant", "consignment"]
        ] = Unset,
        include_related: typing.Union[Unset, bool] = Unset,
    ) -> typing.List[stock_api.FullStockReport]:
        """

        :param limit: Limit the number of entities to retrieve. (Ограничить количество сущностей для извлечения.)
        :param offset: Offset in the returned list of entities. (Отступ в выдаваемом списке сущностей.)
        :param group_by: Type to group by. (Тип, по которому нужно сгруппировать выдачу.)
        :param include_related: Include consignments for product and variants. (Вывод остатков по модификациям и сериям товаров.)
        :return: List of full stock reports (Список отчетов по остаткам)
        """
        return await self(
            stock_api.GetFullStockReportRequest(
                limit=limit,
                offset=offset,
                group_by=group_by,
                include_related=include_related,
            )
        )

    async def get_small_stock_current_report(
        self,
        include: typing.Union[Unset, str] = Unset,
        changed_since: typing.Union[Unset, datetime.datetime] = Unset,
        stock_type: typing.Union[
            Unset, typing.Literal["stock", "freeStock", "quantity"]
        ] = Unset,
        filter_assortment_id: typing.Union[Unset, typing.List[str]] = Unset,
        filter_store_id: typing.Union[Unset, typing.List[str]] = Unset,
    ) -> typing.List[stock_api.SmallStockReport]:
        """

        :param include: Include related entities (Включить связанные сущности)
        :param changed_since: Changed since (Изменено с)
        :param stock_type: Stock type (Тип остатка)
        :param filter_assortment_id: Filter by assortment id (Фильтр по id товара)
        :param filter_store_id: Filter by store id (Фильтр по id склада)
        :return: List of small stock reports (Список отчетов по остаткам)
        """

        return await self(
            stock_api.GetSmallStockReportCurrentRequest(
                include=include,
                changed_since=changed_since,
                stock_type=stock_type,
                filter_assortment_id=filter_assortment_id,
                filter_store_id=filter_store_id,
            )
        )

    # custom entities
    async def create_custom_entity(
        self,
        name: str,
        meta: typing.Union[Unset, types.Meta] = Unset,
    ) -> custom_entity_api.CustomEntity:
        """
        Create custom entity (Создание пользовательского справочника)

        :param name: Name of custom entity (Наименование Пользовательского справочника)
        :param meta: Meta of custom entity (Метаданные Пользовательского справочника)
        :return: Created custom entity (Созданный пользовательский справочник)
        """

        return await self(
            custom_entity_api.CreateCustomEntityRequest(
                name=name,
                meta=meta,
            )
        )

    async def update_custom_entity(
        self,
        metadata_id: str,
        name: typing.Union[Unset, str] = Unset,
        meta: typing.Union[Unset, types.Meta] = Unset,
    ) -> custom_entity_api.CustomEntity:
        """
        Update custom entity (Обновление пользовательского справочника)

        :param metadata_id: ID of custom entity (ID Пользовательского справочника)
        :param name: Name of custom entity (Наименование Пользовательского справочника)
        :param meta: Meta of custom entity (Метаданные Пользовательского справочника)
        :return: Updated custom entity (Обновленный пользовательский справочник)
        """
        return await self(
            custom_entity_api.UpdateCustomEntityRequest(
                metadata_id=metadata_id,
                name=name,
                meta=meta,
            )
        )

    async def delete_custom_entity(self, metadata_id: str) -> None:
        """
        Delete custom entity (Удаление пользовательского справочника)

        :param metadata_id: ID of custom entity (ID Пользовательского справочника)
        :return: None
        """
        return await self(
            custom_entity_api.DeleteCustomEntityRequest(
                metadata_id=metadata_id,
            )
        )

    async def create_custom_entity_element(
        self,
        metadata_id: str,
        name: str,
        code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        meta: typing.Union[Unset, types.Meta] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
    ) -> custom_entity_api.CustomEntityElement:
        """
        Create custom entity element (Создание элемента пользовательского справочника)

        :param metadata_id: ID of the custom entity (ID справочника)
        :param name: Name of the custom entity element (Наименование элемента справочника)
        :param code: Code of the custom entity element (Код элемента справочника)
        :param description: Description of the custom entity element (Описание элемента справочника)
        :param external_code: External code of the custom entity element (Внешний код элемента справочника)
        :param meta: Metadata of the custom entity element (Метаданные элемента справочника)
        :param group: Group of the custom entity element (Отдел элемента справочника)
        :param owner: Owner of the custom entity element (Владелец элемента справочника)
        :param shared: Shared access of the custom entity element (Общий доступ элемента справочника)
        :return: Created custom entity element (Созданный элемент пользовательского справочника)
        """
        return await self(
            custom_entity_api.CreateCustomEntityElementRequest(
                metadata_id=metadata_id,
                name=name,
                code=code,
                description=description,
                external_code=external_code,
                meta=meta,
                group=group,
                owner=owner,
                shared=shared,
            )
        )

    async def update_custom_entity_element(
        self,
        metadata_id: str,
        element_id: str,
        name: typing.Union[Unset, str] = Unset,
        code: typing.Union[Unset, str] = Unset,
        description: typing.Union[Unset, str] = Unset,
        external_code: typing.Union[Unset, str] = Unset,
        meta: typing.Union[Unset, types.Meta] = Unset,
        group: typing.Union[Unset, types.Meta] = Unset,
        owner: typing.Union[Unset, types.Meta] = Unset,
        shared: typing.Union[Unset, bool] = Unset,
    ) -> custom_entity_api.CustomEntityElement:
        """
        Update custom entity element (Обновление элемента пользовательского справочника)

        :param metadata_id: ID of the custom entity (ID справочника)
        :param element_id: ID of the custom entity element (ID элемента справочника)
        :param name: Name of the custom entity element (Наименование элемента справочника)
        :param code: Code of the custom entity element (Код элемента справочника)
        :param description: Description of the custom entity element (Описание элемента справочника)
        :param external_code: External code of the custom entity element (Внешний код элемента справочника)
        :param meta: Metadata of the custom entity element (Метаданные элемента справочника)
        :param group: Group of the custom entity element (Отдел элемента справочника)
        :param owner: Owner of the custom entity element (Владелец элемента справочника)
        :param shared: Shared access of the custom entity element (Общий доступ элемента справочника)
        :return: Updated custom entity element (Обновленный элемент пользовательского справочника)
        """
        return await self(
            custom_entity_api.UpdateCustomEntityElementRequest(
                metadata_id=metadata_id,
                element_id=element_id,
                name=name,
                code=code,
                description=description,
                external_code=external_code,
                meta=meta,
                group=group,
                owner=owner,
                shared=shared,
            )
        )

    async def delete_custom_entity_element(
        self,
        metadata_id: str,
        element_id: str,
    ) -> None:
        """
        Delete custom entity element (Удаление элемента пользовательского справочника)

        :param metadata_id: ID of the custom entity (ID справочника)
        :param element_id: ID of the custom entity element (ID элемента справочника)
        """
        return await self(
            custom_entity_api.DeleteCustomEntityElementRequest(
                metadata_id=metadata_id,
                element_id=element_id,
            )
        )

    async def get_custom_entity_element(
        self,
        metadata_id: str,
        element_id: str,
    ) -> custom_entity_api.CustomEntityElement:
        """
        Get custom entity element (Получение элемента пользовательского справочника)

        :param metadata_id: ID of the custom entity (ID справочника)
        :param element_id: ID of the custom entity element (ID элемента справочника)
        :return: Custom entity element (Элемент пользовательского справочника)
        """
        return await self(
            custom_entity_api.GetCustomEntityElementRequest(
                metadata_id=metadata_id,
                element_id=element_id,
            )
        )

    async def list_custom_entity_elements(
        self,
        metadata_id: str,
        limit: typing.Union[Unset, int] = Unset,
        offset: typing.Union[Unset, int] = Unset,
    ) -> typing.List[custom_entity_api.CustomEntityElement]:
        """
        List custom entity elements (Получение списка элементов пользовательского справочника)

        :param metadata_id: ID of the custom entity (ID справочника)
        :param limit: Limit (Ограничение)
        :param offset: Offset (Смещение)
        :return: List of custom entity elements (Список элементов пользовательского справочника)
        """
        return await self(
            custom_entity_api.GetCustomEntityElementsRequest(
                metadata_id=metadata_id,
                limit=limit,
                offset=offset,
            )
        )

    async def create_webhook(
        self,
        url: str,
        entity_type: str,
        action: str,
        diff_type: typing.Union[Unset, str] = Unset,
    ) -> webhook_api.Webhook:
        """
        Create a webhook

        :param url: URL of webhook (URL вебхука)
        :param entity_type: type of entity (Тип сущности)
        :param action: type of action (Тип действия)
        :param diff_type: diff type for update action (Тип изменения для действия обновления)
        """
        return await self(
            webhook_api.CreateWebhookRequest(
                url=url,
                entity_type=entity_type,
                action=action,
                diff_type=diff_type,
            )
        )

    async def get_webhook(self, webhook_id: str) -> webhook_api.Webhook:
        """
        Get a webhook

        :param webhook_id: ID of webhook (ID вебхука)
        """
        return await self(webhook_api.GetWebhookRequest(webhook_id=webhook_id))

    async def get_webhooks(self) -> typing.List[webhook_api.Webhook]:
        """
        Get webhook
        """
        return await self(webhook_api.GetWebhooksRequest())

    async def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook

        :param webhook_id: ID of webhook (ID вебхука)
        """
        await self(webhook_api.DeleteWebhookRequest(webhook_id=webhook_id))

    async def update_webhook(
        self,
        webhook_id: str,
        url: typing.Union[Unset, str] = Unset,
        entity_type: typing.Union[Unset, str] = Unset,
        action: typing.Union[Unset, str] = Unset,
        diff_type: typing.Union[Unset, str] = Unset,
    ) -> webhook_api.Webhook:
        """
        Update a webhook

        :param webhook_id: ID of webhook (ID вебхука)
        :param url: URL of webhook (URL вебхука)
        :param entity_type: type of entity (Тип сущности)
        :param action: type of action (Тип действия)
        :param diff_type: diff type for update action (Тип изменения для действия обновления)
        """
        return await self(
            webhook_api.UpdateWebhookRequest(
                webhook_id=webhook_id,
                url=url,
                entity_type=entity_type,
                action=action,
                diff_type=diff_type,
            )
        )

 # organization
    async def get_organizations(
        self,
        limit: typing.Union[Unset, int] = Unset,
        offset: typing.Union[Unset, int] = Unset,
    ) -> typing.List[organization_api.Organization]:
        """

        :param limit:  Limit (макс. )
        :param offset: Offset (Смещение)
        :return: List of organization (список организаций)
        """
        return await self(
            organization_api.GetOrganizationsRequest(limit=limit, offset=offset)
        )

    async def get_organization(
        self, organization_id: str
    ) -> organization_api.Organization:
        """

        :param organization_id: ID (идентификатор)
        :return: Organization (организация)
        """
        return await self(
            organization_api.GetOrganizationRequest(organization_id=organization_id)
        )
