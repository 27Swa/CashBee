from datetime import datetime
from enums import PaymentType


class Organizations:
    def __init__(self,n,tp,phone,wid,id = None):
        self.id = id
        self._name = n
        self.org_type = tp   
        self._phone = [phone] 
        self.wid = wid
    @property
    def name(self):
        return self.name
    @property
    def type_(self):
        return self.org_type
    @property
    def phone(self):
        return self._phone
    @phone.setter
    def phone(self,ph):
        self.phone.append(ph)
class OrganizationMapper:
    """Handling transaction data when reading/writing in DB"""
    """ @staticmethod
    def to_dict(tx: Organizations):
        return (
            tx.name,
            tx.type_,
            tx.wid
        )"""

    @staticmethod
    def from_dict(data: tuple,ph):
        return Organizations(
            from_phone=data["user_id"],
            amount=data["amount"],
            tx_type=PaymentType(data["t_type"]),
            to_phone=data["to"],
            dt=datetime.fromisoformat(data["date"]),
            transaction_id=data["transaction_id"],
            phone =[p[0] for p in ph]
        )

