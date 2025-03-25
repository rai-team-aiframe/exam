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
    Generate a modern Excel report for a user with their exam responses
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
        
        # Create an Excel workbook and add worksheets
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Create worksheets with modern names
        summary_sheet = workbook.add_worksheet('خلاصه')
        personality_sheet = workbook.add_worksheet('آزمون شخصیت')
        puzzle_sheet = workbook.add_worksheet('آزمون پازل')
        
        # Define color palette for modern design
        colors = {
            'primary': '#3498db',      # Blue
            'secondary': '#2c3e50',    # Dark blue/gray
            'success': '#2ecc71',      # Green
            'warning': '#f39c12',      # Orange
            'danger': '#e74c3c',       # Red
            'light': '#ecf0f1',        # Light gray
            'dark': '#2c3e50',         # Dark blue/gray
            'white': '#ffffff',        # White
            'light_gray': '#f5f5f5',   # Light gray background
            'border': '#bdc3c7',       # Border color
            'header_bg': '#34495e',    # Header background
            'accent1': '#9b59b6',      # Purple
            'accent2': '#16a085',      # Teal
            'accent3': '#f1c40f',      # Yellow
        }

        # Create formats for the Excel file
        formats = {
            'title': workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['primary'],
                'border': 0,
            }),
            'subtitle': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['secondary'],
                'border': 0,
            }),
            'section_header': workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'right',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['accent1'],
                'border': 0,
            }),
            'header': workbook.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['header_bg'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'header_right': workbook.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['header_bg'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'label': workbook.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['secondary'],
                'bg_color': colors['light_gray'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'value': workbook.add_format({
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['dark'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'date': workbook.add_format({
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['dark'],
                'border': 1,
                'border_color': colors['border'],
                'num_format': 'yyyy/mm/dd',
            }),
            'cell': workbook.add_format({
                'font_size': 11,
                'align': 'right',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_name': 'B Nazanin',
                'border': 1,
                'border_color': colors['border'],
            }),
            'cell_center': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'font_name': 'B Nazanin',
                'border': 1,
                'border_color': colors['border'],
            }),
            'stat_value': workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['primary'],
                'border': 0,
            }),
            'success': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['success'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'warning': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['warning'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'danger': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['danger'],
                'border': 1,
                'border_color': colors['border'],
            }),
            'footer': workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['secondary'],
                'italic': True,
            }),
        }
        
        # Set column widths for summary sheet
        summary_sheet.set_column('A:A', 18)
        summary_sheet.set_column('B:B', 30)
        summary_sheet.set_column('C:C', 15)
        summary_sheet.set_column('D:D', 30)
        summary_sheet.set_column('E:E', 5)  # Spacer column
        summary_sheet.set_column('F:F', 18)
        summary_sheet.set_column('G:G', 15)
        
        # Set column widths for personality sheet
        personality_sheet.set_column('A:A', 8)   # شماره
        personality_sheet.set_column('B:B', 12)  # تاریخ پاسخ
        personality_sheet.set_column('C:C', 10)  # شماره سوال
        personality_sheet.set_column('D:D', 60)  # متن سوال
        personality_sheet.set_column('E:E', 15)  # پاسخ
        
        # Set column widths for puzzle sheet
        puzzle_sheet.set_column('A:A', 8)   # شماره
        puzzle_sheet.set_column('B:B', 12)  # تاریخ پاسخ
        puzzle_sheet.set_column('C:C', 8)   # شماره سوال
        puzzle_sheet.set_column('D:D', 40)  # متن سوال
        puzzle_sheet.set_column('E:E', 20)  # پاسخ
        puzzle_sheet.set_column('F:F', 15)  # امتیاز
        puzzle_sheet.set_column('G:G', 10)  # تعداد تلاش
        
        # Determine today's date
        if JDATETIME_AVAILABLE:
            try:
                today = jdatetime.datetime.now().strftime("%Y/%m/%d")
            except Exception:
                today = datetime.datetime.now().strftime("%Y/%m/%d")
        else:
            today = datetime.datetime.now().strftime("%Y/%m/%d")
        
        # SUMMARY SHEET
        # =============
        
        # Add title
        summary_sheet.merge_range('A1:G1', 'گزارش آزمون شخصیت و هوش', formats['title'])
        summary_sheet.set_row(0, 30)  # Make title row taller
        
        # Add report date
        summary_sheet.write('A2', 'تاریخ گزارش:', formats['label'])
        summary_sheet.write('B2', today, formats['value'])
        
        # Add spacer row
        summary_sheet.set_row(2, 10)
        
        # User Information Section
        summary_sheet.merge_range('A4:G4', 'اطلاعات کاربر', formats['subtitle'])
        summary_sheet.set_row(3, 25)  # Make section header row taller
        
        # User details
        row = 5
        summary_sheet.write(f'A{row}', 'نام کاربری:', formats['label'])
        summary_sheet.write(f'B{row}', user.get('username', ''), formats['value'])
        summary_sheet.write(f'C{row}', 'کد ملی:', formats['label'])
        summary_sheet.write(f'D{row}', user.get('id_number', ''), formats['value'])
        
        row += 1
        summary_sheet.write(f'A{row}', 'نام:', formats['label'])
        summary_sheet.write(f'B{row}', user.get('first_name', ''), formats['value'])
        summary_sheet.write(f'C{row}', 'نام خانوادگی:', formats['label'])
        summary_sheet.write(f'D{row}', user.get('last_name', ''), formats['value'])
        
        row += 1
        summary_sheet.write(f'A{row}', 'تاریخ تولد:', formats['label'])
        summary_sheet.write(f'B{row}', user.get('birth_date', ''), formats['date'])
        summary_sheet.write(f'C{row}', 'شماره تلفن:', formats['label'])
        summary_sheet.write(f'D{row}', user.get('phone_number', ''), formats['value'])
        
        row += 1
        summary_sheet.write(f'A{row}', 'تاریخ ثبت نام:', formats['label'])
        summary_sheet.write(f'B{row}', user.get('created_at', ''), formats['date'])
        
        # Add review information if exists
        if user.get('has_review', False):
            row += 2
            summary_sheet.merge_range(f'A{row}:G{row}', 'نتیجه بررسی', formats['section_header'])
            summary_sheet.set_row(row-1, 20)  # Make section header row taller
            
            row += 1
            summary_sheet.write(f'A{row}', 'متن بررسی:', formats['label'])
            summary_sheet.merge_range(f'B{row}:D{row}', user.get('review_text', ''), formats['cell'])
            
            row += 1
            summary_sheet.write(f'A{row}', 'تاریخ بررسی:', formats['label'])
            summary_sheet.write(f'B{row}', user.get('review_date', ''), formats['date'])
            summary_sheet.write(f'C{row}', 'کارشناس:', formats['label'])
            summary_sheet.write(f'D{row}', user.get('admin_job_field', 'کارشناس'), formats['value'])
        
        # Add spacer row
        row += 2
        
        # Separate personality and puzzle responses
        personality_responses = [r for r in exam_responses if r['question_type'] == 'personality']
        puzzle_responses = [r for r in exam_responses if r['question_type'] == 'puzzle']
        
        # Exam Summary Section
        summary_sheet.merge_range(f'A{row}:G{row}', 'خلاصه آزمون', formats['subtitle'])
        summary_sheet.set_row(row-1, 25)  # Make section header row taller
        
        row += 1
        summary_sheet.write(f'A{row}', 'تعداد کل سوالات:', formats['label'])
        summary_sheet.write(f'B{row}', len(exam_responses), formats['value'])
        
        row += 1
        summary_sheet.write(f'A{row}', 'سوالات شخصیت:', formats['label'])
        summary_sheet.write(f'B{row}', len(personality_responses), formats['value'])
        
        row += 1
        summary_sheet.write(f'A{row}', 'سوالات پازل:', formats['label'])
        summary_sheet.write(f'B{row}', len(puzzle_responses), formats['value'])
        
        # Add a note about detailed answers
        row += 1
        summary_sheet.merge_range(f'A{row}:G{row}', 'برای مشاهده جزئیات پاسخ ها به برگه های "آزمون شخصیت" و "آزمون پازل" مراجعه کنید', formats['cell_center'])
        
        # Add puzzle score statistics if there are puzzle responses
        if puzzle_responses:
            row += 2
            
            # Calculate puzzle statistics
            total_score = sum(float(r.get('score') or 0) for r in puzzle_responses)
            avg_score = total_score / len(puzzle_responses) if len(puzzle_responses) > 0 else 0
            perfect_scores = sum(1 for r in puzzle_responses if r.get('score') == 1.0)
            partial_scores = sum(1 for r in puzzle_responses if r.get('score') == 0.5)
            zero_scores = sum(1 for r in puzzle_responses if r.get('score') == 0.0)
            
            # Add puzzle results section
            summary_sheet.merge_range(f'A{row}:G{row}', 'نتایج پازل', formats['section_header'])
            summary_sheet.set_row(row-1, 20)  # Make section header row taller
            
            # Create a modern stat dashboard
            row += 1
            
            # Row 1 of stats
            summary_sheet.write(f'A{row}', 'امتیاز کل پازل:', formats['label'])
            summary_sheet.write(f'B{row}', f"{total_score} از {len(puzzle_responses)}", formats['stat_value'])
            
            summary_sheet.write(f'F{row}', 'میانگین امتیاز:', formats['label'])
            summary_sheet.write(f'G{row}', f"{avg_score:.2f}", formats['stat_value'])
            
            row += 1
            
            # Row 2 of stats - create a visual representation of scores
            summary_sheet.write(f'A{row}', 'امتیاز کامل:', formats['label'])
            summary_sheet.write(f'B{row}', perfect_scores, formats['success'])
            
            summary_sheet.write(f'C{row}', 'امتیاز نسبی:', formats['label'])
            summary_sheet.write(f'D{row}', partial_scores, formats['warning'])
            
            summary_sheet.write(f'F{row}', 'امتیاز صفر:', formats['label'])
            summary_sheet.write(f'G{row}', zero_scores, formats['danger'])
        
        # Add spacer before footer
        row += 3
        
        # Add footer
        summary_sheet.merge_range(f'A{row}:G{row}', 'این گزارش توسط سیستم آزمون آنلاین شخصیت تولید شده است.', formats['footer'])
        
        # PERSONALITY SHEET
        # =================
        personality_sheet.merge_range('A1:E1', 'آزمون شخصیت', formats['title'])
        personality_sheet.set_row(0, 30)  # Make title row taller
        
        # Add introductory text
        personality_sheet.merge_range('A2:E2', 'این برگه شامل همه سوالات شخصیت و پاسخ های داده شده می باشد', formats['subtitle'])
        
        # Headers
        personality_sheet.write('A3', 'شماره', formats['header'])
        personality_sheet.write('B3', 'تاریخ پاسخ', formats['header'])
        personality_sheet.write('C3', 'شماره سوال', formats['header'])
        personality_sheet.write('D3', 'متن سوال', formats['header_right'])
        personality_sheet.write('E3', 'پاسخ', formats['header'])
        
        # Write personality response data
        for i, response in enumerate(personality_responses):
            row = i + 4  # Start from row 4 (after headers)
            
            personality_sheet.write(f'A{row}', i + 1, formats['cell_center'])
            personality_sheet.write(f'B{row}', response.get('created_at', ''), formats['cell_center'])
            
            # Get question ID from the text (if available)
            question_text = response.get('question_text', '')
            question_id = ''
            if question_text.startswith(tuple(str(i) + "-" for i in range(1, 100))):
                try:
                    question_id = question_text.split('-')[0].strip()
                except:
                    question_id = ''
            
            personality_sheet.write(f'C{row}', question_id, formats['cell_center'])
            personality_sheet.write(f'D{row}', question_text, formats['cell'])
            personality_sheet.write(f'E{row}', response.get('response_text', ''), formats['cell_center'])
        
        # PUZZLE SHEET
        # ============
        puzzle_sheet.merge_range('A1:G1', 'آزمون پازل', formats['title'])
        puzzle_sheet.set_row(0, 30)  # Make title row taller
        
        # Add introductory text
        puzzle_sheet.merge_range('A2:G2', 'این برگه شامل همه سوالات پازل، پاسخ های داده شده و امتیازهای کسب شده می باشد', formats['subtitle'])
        
        # Headers
        puzzle_sheet.write('A3', 'شماره', formats['header'])
        puzzle_sheet.write('B3', 'تاریخ پاسخ', formats['header'])
        puzzle_sheet.write('C3', 'شماره سوال', formats['header'])
        puzzle_sheet.write('D3', 'متن سوال', formats['header_right'])
        puzzle_sheet.write('E3', 'پاسخ', formats['header'])
        puzzle_sheet.write('F3', 'امتیاز', formats['header'])
        puzzle_sheet.write('G3', 'تعداد تلاش', formats['header'])
        
        # Create custom formats for different scores
        score_formats = {
            1.0: workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['success'],
                'border': 1,
                'border_color': colors['border'],
            }),
            0.5: workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['warning'],
                'border': 1,
                'border_color': colors['border'],
            }),
            0.0: workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'font_name': 'B Nazanin',
                'color': colors['white'],
                'bg_color': colors['danger'],
                'border': 1,
                'border_color': colors['border'],
            }),
        }
        
        # Write puzzle response data
        for i, response in enumerate(puzzle_responses):
            row = i + 4  # Start from row 4 (after headers)
            
            puzzle_sheet.write(f'A{row}', i + 1, formats['cell_center'])
            puzzle_sheet.write(f'B{row}', response.get('created_at', ''), formats['cell_center'])
            
            # Get question number
            question_id = response.get('question_id', '')
            
            puzzle_sheet.write(f'C{row}', str(question_id), formats['cell_center'])
            puzzle_sheet.write(f'D{row}', response.get('question_text', ''), formats['cell'])
            puzzle_sheet.write(f'E{row}', response.get('response_text', ''), formats['cell'])
            
            # Use the appropriate format based on score
            score = response.get('score')
            score_format = score_formats.get(score, formats['cell_center'])
            puzzle_sheet.write(f'F{row}', response.get('score_text', ''), score_format)
            
            puzzle_sheet.write(f'G{row}', response.get('attempts_text', ''), formats['cell_center'])
        
        # Set active sheet to the summary sheet
        workbook.worksheets_objs[0].activate()
        
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