/**
 * PDF Forms - Fill Form Fields
 * Fill existing PDF form fields
 */

const { PDFDocument } = require('pdf-lib');

/**
 * Fill PDF form fields
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @param {Array} formFields - Array of {fieldName, value} objects
 * @returns {Promise<Buffer>} Edited PDF buffer
 */
async function fillFormFields(pdfBuffer, formFields) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const form = pdfDoc.getForm();
    
    // Get all form fields
    const fields = form.getFields();
    
    // Fill form fields
    formFields.forEach(({ fieldName, value }) => {
      try {
        const field = form.getTextField(fieldName);
        if (field) {
          field.setText(value);
        }
      } catch (e) {
        try {
          const field = form.getCheckBox(fieldName);
          if (field) {
            if (value === true || value === 'true' || value === 'checked') {
              field.check();
            } else {
              field.uncheck();
            }
          }
        } catch (e2) {
          try {
            const field = form.getRadioGroup(fieldName);
            if (field) {
              field.select(value);
            }
          } catch (e3) {
            console.warn(`Form field "${fieldName}" not found or not supported`);
          }
        }
      }
    });
    
    // Flatten form (make fields non-editable)
    form.flatten();
    
    const editedPdfBytes = await pdfDoc.save();
    return Buffer.from(editedPdfBytes);
  } catch (error) {
    console.error('Error filling form fields:', error);
    throw new Error(`Form filling failed: ${error.message}`);
  }
}

/**
 * Get form fields from PDF
 * @param {Buffer} pdfBuffer - PDF file buffer
 * @returns {Promise<Array>} Array of form field information
 */
async function getFormFields(pdfBuffer) {
  try {
    const pdfDoc = await PDFDocument.load(pdfBuffer);
    const form = pdfDoc.getForm();
    const fields = form.getFields();
    
    const formFields = [];
    fields.forEach(field => {
      const fieldName = field.getName();
      let fieldType = 'unknown';
      let value = null;
      
      try {
        if (field.constructor.name.includes('PDFTextField')) {
          fieldType = 'text';
          value = field.getText();
        } else if (field.constructor.name.includes('PDFCheckBox')) {
          fieldType = 'checkbox';
          value = field.isChecked();
        } else if (field.constructor.name.includes('PDFRadioGroup')) {
          fieldType = 'radio';
          value = field.getSelected();
        }
      } catch (e) {
        // Field type detection failed
      }
      
      formFields.push({
        name: fieldName,
        type: fieldType,
        value: value
      });
    });
    
    return formFields;
  } catch (error) {
    console.error('Error getting form fields:', error);
    return [];
  }
}

module.exports = {
  fillFormFields,
  getFormFields
};

