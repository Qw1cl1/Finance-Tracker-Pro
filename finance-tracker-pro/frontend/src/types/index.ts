export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Transaction {
  id: number;
  title: string;
  amount: number;
  date: string;
  transaction_type: 'income' | 'expense';
  category_id?: number;
  subcategory_id?: number;
  comment?: string;
  user_id: number;
  is_recurring: boolean;
  category?: Category;
}

export interface Category {
  id: number;
  name: string;
  icon: string;
  color: string;
  parent_id?: number;
  user_id: number;
  children?: Category[];
}

export interface RecurringPayment {
  id: number;
  title: string;
  amount: number;
  frequency: 'daily' | 'weekly' | 'monthly' | 'yearly';
  next_payment_date: string;
  last_payment_date?: string;
  category_id?: number;
  user_id: number;
  is_active: boolean;
}

export interface Budget {
  id: number;
  category_id: number;
  limit_amount: number;
  period: string;
  user_id: number;
  start_date: string;
  end_date?: string;
  category?: Category;
  spent_amount?: number;
  is_exceeded?: boolean;
}

export interface Goal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline?: string;
  description?: string;
  icon: string;
  color: string;
  user_id: number;
  is_completed: boolean;
  progress_percentage?: number;
}

export interface DashboardSummary {
  total_balance: number;
  monthly_income: number;
  monthly_expense: number;
  savings: number;
  recent_transactions: Transaction[];
}

export interface AnalyticsResponse {
  categories: CategoryAnalytics[];
  monthly_trends: MonthlyTrend[];
  top_categories: CategoryAnalytics[];
  average_daily_expense: number;
  comparison?: {
    income_change: number;
    expense_change: number;
    current_income: number;
    previous_income: number;
    current_expense: number;
    previous_expense: number;
  };
}

export interface CategoryAnalytics {
  category_id: number;
  category_name: string;
  total_amount: number;
  transaction_count: number;
  percentage: number;
  color?: string;
}

export interface MonthlyTrend {
  month: string;
  income: number;
  expense: number;
  net: number;
}

export interface Insight {
  message: string;
  type: 'warning' | 'info' | 'success';
  category?: string;
}
