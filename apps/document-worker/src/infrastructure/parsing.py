import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.config import settings


class Sheet:
    def __init__(self, name: str, columns: list[str], df: pd.DataFrame) -> None:
        self.name = name
        self.columns = columns
        self.df = df
    
    # converts DataFrame rows to strings 
    # in format 'column: "value", column: "value"...'
    def _rows_to_lines(self) -> list[str]:
        lines = []
        for _, row in self.df.iterrows():
            line_parts = []
            for col in self.df.columns:
                val = row[col]
                line_parts.append(f'"{col}": "{val}"')
            line = ", ".join(line_parts)
            lines.append(line)
        return lines

    # create text chunks containing sheet metadata and rows
    def create_chunks(self) -> list[str]:
        chunk_size = settings.DOCUMENT_CHUNK_ROWS
        chunks: list[str] = []
        chunk_metadata = "\n".join([
            f'Sheet: "{self.name}"',
            f'Columns: ["{ '", "'.join(self.columns) }"]',
            "Data:",
        ])
        sheet_lines = self._rows_to_lines()
        if len(sheet_lines) == 0:
            # if sheet is empty, create a chunk with just metadata
            chunks.append(chunk_metadata + "No data rows")
        else:
            for i in range(0, len(sheet_lines), chunk_size):
                chunk_lines = [chunk_metadata] + sheet_lines[i:i+chunk_size]
                chunk_content = "\n".join(chunk_lines)
                chunks.append(f"{chunk_metadata}\n{chunk_content}")
        return chunks


executor = ThreadPoolExecutor()  # global executor for chunk creation

# For each sheet, create chunks of text with metadata for vector search. Each chunk will contain DOCUMENT_CHUNK_ROWS rows from the sheet.
async def create_chunks_from_sheets_async(sheets: list[Sheet]) -> list[str]:
    loop = asyncio.get_running_loop()
    # run all sheet chunking in parallel threads
    tasks = [loop.run_in_executor(executor, sheet.create_chunks) for sheet in sheets]
    # wait for all tasks to complete
    results: list[list[str]] = await asyncio.gather(*tasks)
    # flatten the list of lists
    chunks: list[str] = []
    for sheet_chunks in results:
        chunks.extend(sheet_chunks)
    return chunks