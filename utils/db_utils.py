import psycopg2
from psycopg2 import sql
from fastapi import HTTPException
from configs.config import Config
from typing import List, Dict, Any


def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        return connection
    except Exception as e:
        raise HTTPException(status_code=441, detail=f"Error connecting to the database: {e}")


def add_record_to_db(table_name, record):
    if not record:
        raise HTTPException(status_code=442, detail="No record provided")

    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=443, detail="Connection failed")

    try:
        cursor = connection.cursor()
        columns = record.keys()

        placeholders = ", ".join(["%s" for _ in columns])
        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(placeholders)
        )

        values = tuple(record[col] for col in columns)

        cursor.execute(insert_query, values)
        new_id = cursor.fetchone()[0]
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": f"Successfully added record to the table {table_name}", "record_id": new_id, "success": True}

    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=444, detail=f"Error adding record to the database: {e}")


def delete_records_from_db(table_name, id_list):
    if not id_list:
        raise HTTPException(status_code=442, detail="No IDs provided for deletion")

    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=443, detail="Connection failed")

    try:
        cursor = connection.cursor()
        placeholders = sql.SQL(", ").join(sql.Placeholder() * len(id_list))
        delete_query = sql.SQL("DELETE FROM {} WHERE id IN ({})").format(
            sql.Identifier(table_name), placeholders
        )

        cursor.execute(delete_query, id_list)
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": f"Successfully deleted {len(id_list)} records from the table {table_name}", "success": True}

    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=446, detail=f"Error deleting records from the database: {e}")

def update_records_in_db(table_name, records):
    if not records:
        raise HTTPException(status_code=442, detail="No records provided for update")

    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=443, detail="Connection failed")

    try:
        cursor = connection.cursor()

        for record in records:
            if 'id' not in record:
                raise HTTPException(status_code=447, detail=f"Record {record} does not contain an 'id' field")

            record_id = record.pop('id')
            set_clause = sql.SQL(", ").join([
                sql.SQL("{} = %s").format(sql.Identifier(col)) for col in record.keys()
            ])
            update_query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(
                sql.Identifier(table_name), set_clause
            )
            values = list(record.values()) + [record_id]

            cursor.execute(update_query, values)

        connection.commit()

        cursor.close()
        connection.close()

        return {"message": f"Successfully updated {len(records)} records in the table {table_name}", "success": True}

    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=448, detail=f"Error updating records in the database: {e}")

def get_records_from_db(table_name: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=443, detail="Connection failed")

    try:
        cursor = connection.cursor()

        query = sql.SQL("SELECT * FROM {} ").format(sql.Identifier(table_name))
        query_params = []

        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, list):
                    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(value))
                    where_clauses.append(sql.SQL("{} IN ({})").format(sql.Identifier(key), placeholders))
                    query_params.extend(value)
                else:
                    where_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(key)))
                    query_params.append(value)

            where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)
            query += where_clause

        cursor.execute(query, query_params)
        columns = [desc[0] for desc in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        connection.close()

        return records

    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=449, detail=f"Error retrieving records from the database: {e}")


def get_all_records_from_db(table_name: str) -> List[Dict[str, Any]]:
    connection = get_db_connection()
    if connection is None:
        raise HTTPException(status_code=443, detail="Connection failed")

    try:
        cursor = connection.cursor()
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name))

        cursor.execute(query)
        records = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]  # Pobranie nazw kolumn

        cursor.close()
        connection.close()

        return [dict(zip(columns, record)) for record in records]

    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=449, detail=f"Error fetching records from the database: {e}")

