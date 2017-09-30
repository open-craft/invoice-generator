Invoice generator
=================

This program creates an invoice with the items from your JIRA work sheet. It includes subtotals per project.

The requirements are Python 3, Latex, Gnumeric (for the xls-to-csv conversion) and some Python packages (dateutil, Jinja2, PyYAML).


Instructions
------------
 
1. Fill in your hourly rate in `config.yaml`.
           
2. Edit the Latex template file opencraft.tex. At the very least, you need to write your address, replace all the ellipses with more useful data and add a file signature.png with your signature.
           
3. Download your timesheet in Excel format by going to the timesheet for the correct month in JIRA and using the "Export" menu in the top right corner.
           
4. Run the following command line:
    
    ```
    ./main.py new data_file="path/to/timesheet/data.xls" from_date=2015-06-01 to_date=2015-06-30
    ```

5. This will create a PDF with your invoice, if all goes well.
           
           
