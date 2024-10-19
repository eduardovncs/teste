"""
    Programa para testes
"""
from typing import List

def sum_values(paramn: List[int]=None) -> int:
    """
        Soma de valores.

        Args:
            paramn: Lista com valores a serem somados

        Returns:
            Soma dos valores da lista
    """

    if not paramn:
        paramn = []
    return sum(paramn)
