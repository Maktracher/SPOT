from dataclasses import dataclass
from enum import Enum, auto


class AssetType(Enum):
    CRYPTO = "crypto"
    STOCK = "stock"


class Asset(Enum):
    # Crypto Assets
    BTC = ("BTC/USDT", AssetType.CRYPTO)
    ETH = ("ETH/USDT", AssetType.CRYPTO)
    SOL = ("SOL/USDT", AssetType.CRYPTO)
    XRP = ("XRP/USDT", AssetType.CRYPTO)
    BNB = ("BNB/USDT", AssetType.CRYPTO)
    DOGE = ("DOGE/USDT", AssetType.CRYPTO)
    ADA = ("ADA/USDT", AssetType.CRYPTO)
    LINK = ("LINK/USDT", AssetType.CRYPTO)
    SUI = ("SUI/USDT", AssetType.CRYPTO)
    WLD = ("WLD/USDT", AssetType.CRYPTO)
    ONDO = ("ONDO/USDT", AssetType.CRYPTO)
    TAO = ("TAO/USDT", AssetType.CRYPTO)
    PEPE = ("PEPE/USDT", AssetType.CRYPTO)

    # bStock / Stocks
    NVDA = ("NVDAB/USDT", AssetType.STOCK)
    TSM = ("TSMB/USDT", AssetType.STOCK)
    AVGO = ("AVGOB/USDT", AssetType.STOCK)
    MU = ("MUUB/USDT", AssetType.STOCK)
    MSFT = ("MSFTB/USDT", AssetType.STOCK)
    AMZN = ("AMZNB/USDT", AssetType.STOCK)
    AMAT = ("AMATB/USDT", AssetType.STOCK)
    MRVL = ("MRVLB/USDT", AssetType.STOCK)
    PLTR = ("PLTRB/USDT", AssetType.STOCK)
    ARM = ("ARMB/USDT", AssetType.STOCK)
    CRWV = ("CRWVB/USDT", AssetType.STOCK)
    RKLB = ("RKLBB/USDT", AssetType.STOCK)
    CRCL = ("CRCLB/USDT", AssetType.STOCK)

    @property
    def symbol(self) -> str:
        return self.value[0]

    @property
    def asset_type(self) -> AssetType:
        return self.value[1]

    @property
    def base_currency(self) -> str:
        return self.symbol.split("/")[0]

    @property
    def quote_currency(self) -> str:
        return self.symbol.split("/")[1]


class SignalType(Enum):
    BUY = auto()
    SELL = auto()
    CANCEL_BUY = auto()
    CANCEL_SELL = auto()
    HOLD = auto()


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class TradingSignal:
    asset: Asset
    signal_type: SignalType
    rsi: float
    fgi: int
    current_price: float
    atr: float
    score: float = 0.0


@dataclass(frozen=True)
class GridOrderParams:
    asset: Asset
    side: OrderSide
    price: float
    quantity: float
    offset_percent: float


@dataclass(frozen=True)
class Balance:
    currency: str
    free: float
    used: float

    @property
    def total(self) -> float:
        return self.free + self.used