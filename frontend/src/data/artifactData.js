export const demoArtifacts = [
    {
        id: 'product.py',
        type: 'Python',
        agent: 'CodingAgent',
        task: 't-1',
        createdAt: '20:35:42',
        content: `class Product:\n    def __init__(self, id: str, name: str, price: float):\n        self.id = id\n        self.name = name\n        self.price = price\n\n    def to_dict(self):\n        return {\n            "id": self.id,\n            "name": self.name,\n            "price": self.price\n        }`
    },
    {
        id: 'database.py',
        type: 'Python',
        agent: 'CodingAgent',
        task: 't-2',
        createdAt: '20:37:10',
        content: `from sqlalchemy import Column, String, Float\nfrom database import Base\n\nclass ProductModel(Base):\n    __tablename__ = "products"\n    id = Column(String, primary_key=True)\n    name = Column(String)\n    price = Column(Float)`
    }
];
