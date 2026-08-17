from rest_framework import serializers
from .models import Employee, Payslip

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'position', 'basic_salary', 'hire_date',
            'status', 'salary_account', 'payment_account', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class PayslipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'fiscal_period', 'basic_salary',
            'allowances', 'deductions', 'net_salary', 'journal_entry',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['net_salary', 'journal_entry', 'created_at', 'updated_at']

    def validate(self, data):
        instance = Payslip(**data)
        instance.clean()
        return data
