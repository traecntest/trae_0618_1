from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field as PydanticField
from .base import BaseModel


class FieldType(str, Enum):
    INT = "int"
    STRING = "string"
    TEXT = "text"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    FOREIGN_KEY = "foreign_key"


class RelationType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class DataField(BaseModel):
    name: str = ""
    field_type: str = "string"
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    default_value: Any = None
    length: Optional[int] = None
    comment: str = ""
    foreign_table: Optional[str] = None
    foreign_field: Optional[str] = None
    position: Dict[str, int] = PydanticField(default_factory=dict)

    @classmethod
    def create(cls, name: str, field_type: str, **kwargs) -> "DataField":
        return cls(name=name, field_type=field_type, **kwargs)


Field = DataField


class Index(BaseModel):
    name: str = ""
    fields: List[str] = PydanticField(default_factory=list)
    unique: bool = False


class TableSchema(BaseModel):
    name: str = ""
    fields: List[DataField] = PydanticField(default_factory=list)
    indexes: List[Index] = PydanticField(default_factory=list)
    position: Dict[str, int] = PydanticField(default_factory=lambda: {"x": 0, "y": 0})
    color: str = "#1890ff"

    def add_field(self, name: str, field_type: str, **kwargs) -> DataField:
        field = Field.create(name, field_type, **kwargs)
        self.fields.append(field)
        return field

    def remove_field(self, field_id: str) -> None:
        self.fields = [f for f in self.fields if f.id != field_id]

    def get_field(self, field_id: str) -> Optional[Field]:
        for field in self.fields:
            if field.id == field_id:
                return field
        return None

    def has_primary_key(self) -> bool:
        return any(f.primary_key for f in self.fields)


class Relation(BaseModel):
    name: str = ""
    source_table: str = ""
    target_table: str = ""
    source_field: str = ""
    target_field: str = ""
    relation_type: str = "one_to_many"
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"

    @classmethod
    def create(cls, source_table: str, target_table: str, relation_type: str, **kwargs) -> "Relation":
        return cls(
            source_table=source_table,
            target_table=target_table,
            relation_type=relation_type,
            **kwargs
        )


class DataModel(BaseModel):
    name: str = "新建数据模型"
    description: str = ""
    tables: List[TableSchema] = PydanticField(default_factory=list)
    relations: List[Relation] = PydanticField(default_factory=list)

    def add_table(self, name: str, **kwargs) -> TableSchema:
        if "id" not in kwargs:
            pass
        table = TableSchema(name=name, **kwargs)
        if not table.has_primary_key():
            table.add_field("id", "int", primary_key=True, nullable=False)
        self.tables.append(table)
        return table

    def remove_table(self, table_id: str) -> None:
        self.tables = [t for t in self.tables if t.id != table_id]
        self.relations = [
            r for r in self.relations 
            if r.source_table != table_id and r.target_table != table_id
        ]

    def get_table(self, table_id: str) -> Optional[TableSchema]:
        for table in self.tables:
            if table.id == table_id:
                return table
        return None

    def get_table_by_name(self, name: str) -> Optional[TableSchema]:
        for table in self.tables:
            if table.name == name:
                return table
        return None

    def add_relation(self, source_table: str, target_table: str, relation_type: str, **kwargs) -> Relation:
        relation = Relation.create(source_table, target_table, relation_type, **kwargs)
        self.relations.append(relation)
        return relation

    def generate_sql(self) -> str:
        sql_statements = []
        
        for table in self.tables:
            fields_sql = []
            for field in table.fields:
                field_sql = self._field_to_sql(field)
                fields_sql.append(field_sql)
            
            for index in table.indexes:
                index_sql = self._index_to_sql(index, table.name)
                if index_sql:
                    sql_statements.append(index_sql)
            
            table_sql = f"CREATE TABLE IF NOT EXISTS {table.name} (\n    "
            table_sql += ",\n    ".join(fields_sql)
            table_sql += "\n);"
            sql_statements.append(table_sql)
        
        for relation in self.relations:
            fk_sql = self._relation_to_sql(relation)
            if fk_sql:
                sql_statements.append(fk_sql)
        
        return "\n\n".join(sql_statements)

    def _field_to_sql(self, field: Field) -> str:
        type_map = {
            "int": "INTEGER",
            "string": f"VARCHAR({field.length or 255})",
            "text": "TEXT",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
            "datetime": "DATETIME",
            "date": "DATE",
            "foreign_key": "INTEGER",
        }
        
        sql_type = type_map.get(field.field_type, "TEXT")
        sql = f"{field.name} {sql_type}"
        
        if field.primary_key:
            sql += " PRIMARY KEY"
            if field.field_type == "int":
                sql += " AUTOINCREMENT"
        
        if not field.nullable:
            sql += " NOT NULL"
        
        if field.unique:
            sql += " UNIQUE"
        
        if field.default_value is not None:
            if isinstance(field.default_value, str):
                sql += f" DEFAULT '{field.default_value}'"
            else:
                sql += f" DEFAULT {field.default_value}"
        
        if field.comment:
            sql += f" -- {field.comment}"
        
        return sql

    def _index_to_sql(self, index: Index, table_name: str) -> str:
        if not index.fields:
            return ""
        unique = "UNIQUE " if index.unique else ""
        fields = ", ".join(index.fields)
        index_name = index.name or f'idx_{table_name}_{hash(tuple(index.fields))}'
        return f"CREATE {unique}INDEX IF NOT EXISTS {index_name} ON {table_name} ({fields});"

    def _relation_to_sql(self, relation: Relation) -> str:
        source_table = self.get_table_by_name(relation.source_table)
        if not source_table:
            return ""
        
        return (
            f"ALTER TABLE {relation.source_table} "
            f"ADD FOREIGN KEY ({relation.source_field}) "
            f"REFERENCES {relation.target_table}({relation.target_field}) "
            f"ON DELETE {relation.on_delete} ON UPDATE {relation.on_update};"
        )
