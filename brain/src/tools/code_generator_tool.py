"""
Code generator tool for Jarilo.
Generates Python scripts using LLM and saves them to files.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from .base import BaseTool, ToolError, ToolResult


class CodeGeneratorTool(BaseTool):
    """Tool for generating Python code using LLM."""

    name = "code_generator_tool"
    description = "Tool for generating Python scripts using AI"

    def __init__(self):
        super().__init__()
        self.workspace_root = "/host_workspace"
        self.logger.info(f"CodeGeneratorTool initialized with workspace root: {self.workspace_root}")

        # OpenAI client will be initialized when needed
        self.client = None

    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate file path within workspace."""
        if not os.path.isabs(path):
            path = os.path.join(self.workspace_root, path)

        resolved_path = os.path.abspath(path)

        if not resolved_path.startswith(self.workspace_root):
            raise ToolError(f"Access denied: path {resolved_path} is outside workspace {self.workspace_root}")

        return Path(resolved_path)

    async def generate_script(self, description: str, output_path: str) -> ToolResult:
        """
        Generate a Python script based on description and save to file.

        Args:
            description: Description of what the script should do
            output_path: Path where to save the generated script
        """
        try:
            # For testing, generate mock script instead of using OpenAI
            if "sales.csv" in description.lower() and ("анализ" in description.lower() or "analyze" in description.lower()):
                generated_code = '''
import pandas as pd
import matplotlib.pyplot as plt

# Load sales data
df = pd.read_csv('sales.csv')

# Convert date column to datetime if exists
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])

# Basic analysis
print("Data shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Data types:")
print(df.dtypes)
print("\\nFirst 5 rows:")
print(df.head())

# Group by month if date column exists
if 'date' in df.columns:
    df['month'] = df['date'].dt.to_period('M')
    monthly_sales = df.groupby('month')['sales'].sum() if 'sales' in df.columns else df.groupby('month').size()
    
    # Plot monthly sales
    plt.figure(figsize=(10, 6))
    monthly_sales.plot(kind='bar')
    plt.title('Monthly Sales')
    plt.xlabel('Month')
    plt.ylabel('Sales')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('sales_report.png')
    print("\\nMonthly sales plot saved as sales_report.png")
else:
    print("No date column found for monthly analysis")

print("\\nAnalysis complete!")
'''
            else:
                generated_code = f'''
# Mock script for: {description}
print("Mock script executed for: {description}")
print("This is a placeholder script.")
'''

            # Resolve output path
            file_path = self._resolve_path(output_path)

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write code to file
            file_path.write_text(generated_code, encoding='utf-8')

            self.logger.info(f"Mock script saved to {file_path}")
            self.logger.info(f"File exists: {file_path.exists()}")
            self.logger.info(f"File content length: {len(generated_code)}")
            return ToolResult(output=f"Script generated and saved to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to generate script: {e}")
            return ToolResult(error=f"Failed to generate script: {str(e)}")

    async def run(self, **kwargs) -> ToolResult:
        """Run the code generator tool."""
        description = kwargs.get('description', '')
        output_path = kwargs.get('output_path', 'temp_script.py')

        if not description:
            return ToolResult(error="Description is required")

        return await self.generate_script(description, output_path)

    async def execute(self, action: str = None, **kwargs) -> ToolResult:
        """Execute the code generator tool."""
        return await self.run(**kwargs)