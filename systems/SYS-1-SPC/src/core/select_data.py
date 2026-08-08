import duckdb
import pathlib as Path

def show_table(product: str, scale: int, process_step: str, batch: list[str]):
     MART_DB_PATH = (
            Path(__file__).resolve().parents[4] / "pipeline" / "models" / "mart"
        )
    
        # 基本架構
        table_parts = f"mart_{product}_{process_step}"
    
        # 如果有 scale，就加進去
        if scale:
            table_parts.append(scale)
    
        # 如果有 version，就加進去
        if version:
            table_parts.append(version)
    
        # 用底線把所有部分串接起來
        MART_TABLE = "_".join(table_parts)
    
        return MART_DB_PATH, MART_TABLE

def select_single_process_step(product: str, scale: int, process_step: str, batch: list[str]):
