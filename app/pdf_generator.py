# app/pdf_generator.py
from io import BytesIO
import datetime
from typing import Dict, List, Any
import xlsxwriter

# Try to import jdatetime, but use regular datetime if not available
try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    JDATETIME_AVAILABLE = False

def generate_user_report_pdf(user: Dict[str, Any], exam_responses: List[Dict[str, Any]]) -> BytesIO:
    """
    Generate an Excel report for a user with their exam responses
    Despite the function name, it actually generates an Excel file
    
    Args:
        user (Dict[str, Any]): User details
        exam_responses (List[Dict[str, Any]]): List of exam responses with question text
        
    Returns:
        BytesIO: Excel file buffer
    """
    try:
        # Create a byte stream to store the Excel file
        output = BytesIO()
        
        # Create an Excel workbook and add a worksheet
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('گزارش کاربر')
        
        # Create formats for the Excel file
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        date_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': 'yyyy/mm/dd'
        })
        
        # Adjust column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 50)
        worksheet.set_column('G:G', 15)
        
        # Determine today's date
        if JDATETIME_AVAILABLE:
            try:
                today = jdatetime.datetime.now().strftime("%Y/%m/%d")
            except Exception:
                today = datetime.datetime.now().strftime("%Y/%m/%d")
        else:
            today = datetime.datetime.now().strftime("%Y/%m/%d")
        
        # Write the title
        worksheet.merge_range('A1:G1', 'گزارش آزمون شخصیت', title_format)
        worksheet.write('A2', f'تاریخ گزارش: {today}', cell_format)
        
        # Write user information section title
        worksheet.merge_range('A4:G4', 'اطلاعات کاربر', title_format)
        
        # Write user information headers
        row = 5
        worksheet.write('A5', 'نام کاربری:', header_format)
        worksheet.write('B5', user.get('username', ''), cell_format)
        worksheet.write('C5', 'کد ملی:', header_format)
        worksheet.write('D5', user.get('id_number', ''), cell_format)
        
        row += 1
        worksheet.write(f'A{row}', 'نام:', header_format)
        worksheet.write(f'B{row}', user.get('first_name', ''), cell_format)
        worksheet.write(f'C{row}', 'نام خانوادگی:', header_format)
        worksheet.write(f'D{row}', user.get('last_name', ''), cell_format)
        
        row += 1
        worksheet.write(f'A{row}', 'تاریخ تولد:', header_format)
        worksheet.write(f'B{row}', user.get('birth_date', ''), cell_format)
        worksheet.write(f'C{row}', 'شماره تلفن:', header_format)
        worksheet.write(f'D{row}', user.get('phone_number', ''), cell_format)
        
        row += 1
        worksheet.write(f'A{row}', 'تاریخ ثبت نام:', header_format)
        worksheet.write(f'B{row}', user.get('created_at', ''), cell_format)
        
        # Add a little space
        row += 2
        
        # Write exam responses section title
        worksheet.merge_range(f'A{row}:G{row}', 'پاسخ های آزمون', title_format)
        row += 1
        
        # Write exam response headers
        worksheet.write(f'A{row}', 'شماره', header_format)
        worksheet.write(f'B{row}', 'تاریخ پاسخ', header_format)
        worksheet.write(f'C{row}', 'شماره سوال', header_format)
        worksheet.merge_range(f'D{row}:F{row}', 'متن سوال', header_format)
        worksheet.write(f'G{row}', 'پاسخ', header_format)
        
        # Write exam responses
        for i, response in enumerate(exam_responses):
            row += 1
            worksheet.write(f'A{row}', i + 1, cell_format)
            
            # Write created_at date
            created_at = response.get('created_at', '')
            worksheet.write(f'B{row}', created_at, cell_format)
            
            # Get question ID from the text (if available)
            question_text = response.get('question_text', '')
            question_id = ''
            if question_text.startswith(tuple(str(i) + "-" for i in range(1, 100))):
                try:
                    question_id = question_text.split('-')[0].strip()
                except:
                    question_id = ''
            
            worksheet.write(f'C{row}', question_id, cell_format)
            worksheet.merge_range(f'D{row}:F{row}', question_text, cell_format)
            worksheet.write(f'G{row}', response.get('response_text', ''), cell_format)
        
        # Add footer
        row += 2
        worksheet.merge_range(f'A{row}:G{row}', 'این گزارش توسط سیستم آزمون آنلاین شخصیت تولید شده است.', cell_format)
        
        # Close the workbook to write the content to the BytesIO object
        workbook.close()
        
        # Reset the file pointer
        output.seek(0)
        
        return output
    
    except Exception as e:
        # Print error for debugging
        print(f"Error generating Excel: {e}")
        
        # Create a simple error Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Error')
        
        worksheet.write('A1', f"Error generating Excel report: {str(e)}")
        workbook.close()
        
        output.seek(0)
        return output