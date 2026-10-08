from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DisputeCase, Transaction

# Demo cases, identical to the ones on rulebookrag.higgsfield.app
CASES = [
    {
        "id": "DSP-0847",
        "chip": "Fraud · Technodom",
        "complaint": "Обнаружил списание 147 500 ₸ в Technodom.kz. Я не совершал покупку, был на работе. Карту никому не передавал.",
        "tx": [
            ("Technodom.kz", "147 500 ₸", "21.09.2026 14:22", "3D-Secure: Нет", "Online"),
            ("Magnum Cash&Carry", "8 900 ₸", "21.09.2026 18:45", "Chip+PIN", "POS"),
        ],
        "type": "Несанкционированная транзакция (фрод)",
        "decision": "Автоматический возврат",
        "dclass": "green",
        "risk": 82,
        "conf": 91,
        "reason": "Транзакция 147 500 ₸ в Technodom.kz проведена без 3D-Secure через онлайн-канал. Другие транзакции — контактные (Chip+PIN), подтверждая присутствие клиента в другом месте.",
        "actions": [
            "Заблокировать карту, оформить перевыпуск",
            "Возврат 147 500 ₸ на счёт",
            "Направить fraud report в платёжную сеть",
        ],
        "letter": "Уважаемый клиент!\n\nПо обращению DSP-0847 транзакция 147 500 ₸ признана несанкционированной. Средства будут возвращены в течение 3 рабочих дней. Карта заблокирована.\n\nС уважением, Служба безопасности",
    },
    {
        "id": "DSP-0846",
        "chip": "ATM · 200K",
        "complaint": "Банкомат не выдал деньги — запросила 200 000 ₸, экран завис, карту вернул, но деньги списались.",
        "tx": [
            ("ATM Forte Абая/Манаса", "200 000 ₸", "21.09.2026 14:30", "Chip+PIN", "ATM"),
        ],
        "type": "Невыдача наличных",
        "decision": "Расследование",
        "dclass": "orange",
        "risk": 45,
        "conf": 78,
        "reason": "Транзакция зафиксирована как settled. Банкомат другого банка — необходим запрос журнала ATM и сверка кассеты. Срок ответа до 15 дней.",
        "actions": [
            "Запрос в банк-владелец ATM",
            "Запросить видеозапись",
            "Уведомить клиента о сроках",
        ],
        "letter": "Уважаемый клиент!\n\nПо обращению DSP-0846 принята заявка о невыдаче 200 000 ₸. Направлен запрос в банк-владелец. Срок — до 15 рабочих дней.\n\nС уважением, Отдел претензий",
    },
    {
        "id": "DSP-0844",
        "chip": "Дубль · Glovo",
        "complaint": "Двойное списание в Glovo — 7 800 ₸ дважды за один заказ. Второе через 3 минуты.",
        "tx": [
            ("Glovo KZ", "7 800 ₸", "20.09.2026 19:12", "Apple Pay", "InApp"),
            ("Glovo KZ", "7 800 ₸", "20.09.2026 19:15", "Apple Pay", "InApp"),
        ],
        "type": "Двойное списание",
        "decision": "Автовозврат дубликата",
        "dclass": "green",
        "risk": 25,
        "conf": 97,
        "reason": "Две идентичные транзакции к Glovo на 7 800 ₸ с разницей 3 минуты через Apple Pay. Классический duplicate charge.",
        "actions": [
            "Автовозврат 7 800 ₸ по дубликату",
            "Уведомить мерчант Glovo о дублировании",
        ],
        "letter": "Уважаемый клиент!\n\nПо обращению DSP-0844 подтверждаем двойное списание. Дубликат 7 800 ₸ вернётся в течение 1 рабочего дня.\n\nС уважением, Служба поддержки",
    },
    {
        "id": "DSP-0841",
        "chip": "Серия · Steam",
        "complaint": "5 транзакций в Steam за ночь на 82 000 ₸ — с 2:00 до 4:00. Я спал. Карту заблокировал утром.",
        "tx": [
            ("STEAM", "24 990 ₸", "18.09 02:14", "Без 3DS", "Online"),
            ("STEAM", "19 990 ₸", "18.09 02:38", "Без 3DS", "Online"),
            ("STEAM", "14 990 ₸", "18.09 03:05", "Без 3DS", "Online"),
            ("STEAM", "12 990 ₸", "18.09 03:31", "Без 3DS", "Online"),
            ("STEAM", "9 040 ₸", "18.09 03:52", "Без 3DS", "Online"),
        ],
        "type": "Серия фрод-транзакций",
        "decision": "Немедленный возврат",
        "dclass": "green",
        "risk": 95,
        "conf": 95,
        "reason": "5 транзакций Steam (82 000 ₸) ночью без 3D-Secure. Типичная компрометация: один мерчант, ночное время, нет аутентификации.",
        "actions": [
            "Возврат 82 000 ₸",
            "Блокировка + перевыпуск карты",
            "Fraud report по 5 транзакциям",
            "Передать в AntiFraud",
        ],
        "letter": "Уважаемый клиент!\n\nПо обращению DSP-0841 все 5 транзакций Steam (82 000 ₸) признаны несанкционированными. Возврат в течение 3 дней. Карта заблокирована.\n\nС уважением, Служба безопасности",
    },
]


def seed(db: Session) -> None:
    if db.scalar(select(DisputeCase.id).limit(1)) is not None:
        return
    for position, c in enumerate(CASES):
        db.add(
            DisputeCase(
                id=c["id"],
                position=position,
                chip=c["chip"],
                complaint=c["complaint"],
                dispute_type=c["type"],
                decision=c["decision"],
                decision_class=c["dclass"],
                risk=c["risk"],
                confidence=c["conf"],
                reasoning=c["reason"],
                actions=c["actions"],
                letter=c["letter"],
                transactions=[
                    Transaction(merchant=m, amount=a, date=d, auth=auth, channel=ch)
                    for m, a, d, auth, ch in c["tx"]
                ],
            )
        )
    db.commit()
