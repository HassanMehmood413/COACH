from typing import List, Dict
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class StartupAnalytics:
    @staticmethod
    async def analyze_market_size(industry: str) -> Dict:
        """Get market size and growth data for an industry"""
        # Example implementation using financial data
        try:
            # Get relevant ETF data as market proxy
            etf_mapping = {
                "tech": "XLK",
                "healthcare": "XLV",
                "fintech": "FINX",
                # Add more industries...
            }
            
            if industry.lower() in etf_mapping:
                etf = yf.Ticker(etf_mapping[industry.lower()])
                data = etf.history(period="2y")
                growth = ((data['Close'][-1] / data['Close'][0]) - 1) * 100
                
                return {
                    "market_growth": f"{growth:.1f}%",
                    "market_size": "Analysis based on ETF performance",
                    "trend": "Growing" if growth > 0 else "Declining"
                }
        except Exception as e:
            print(f"Market analysis error: {e}")
        return {}

    @staticmethod
    def generate_financial_projection(
        current_revenue: float,
        growth_rate: float,
        periods: int = 12
    ) -> Dict:
        """Generate financial projections"""
        projections = []
        revenue = current_revenue
        
        for i in range(periods):
            revenue *= (1 + growth_rate)
            projections.append(round(revenue, 2))
            
        return {
            "revenue_projections": projections,
            "total_growth": f"{((projections[-1]/current_revenue) - 1) * 100:.1f}%",
            "period": "monthly" if periods == 12 else "quarterly"
        }

class CompetitorAnalysis:
    @staticmethod
    async def get_competitor_info(competitor_name: str) -> Dict:
        """Get public information about competitors"""
        try:
            company = yf.Ticker(competitor_name)
            info = company.info
            
            return {
                "name": info.get('longName', competitor_name),
                "market_cap": info.get('marketCap', 'N/A'),
                "revenue": info.get('totalRevenue', 'N/A'),
                "employees": info.get('fullTimeEmployees', 'N/A')
            }
        except:
            return {} 