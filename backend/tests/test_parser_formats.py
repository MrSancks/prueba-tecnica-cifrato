"""
Test para verificar que el parser funciona con diferentes formatos de XML de la DIAN
"""
from pathlib import Path
from app.infrastructure.services.invoice_parser import UBLInvoiceParser

def test_all_formats():
    parser = UBLInvoiceParser()
    
    test_files = [
        ("sales-invoice-1.xml", "Invoice"),
        ("standard-invoice-2.xml", "Invoice"),
        ("credit-note-1.xml", "CreditNote"),
    ]
    
    for filename, expected_type in test_files:
        print(f"\n{'='*60}")
        print(f"Testeando: {filename}")
        print(f"{'='*60}")
        
        xml_path = Path(f"app/assessment-files/{filename}")
        if not xml_path.exists():
            print(f"❌ Archivo no encontrado: {xml_path}")
            continue
        
        try:
            xml_bytes = xml_path.read_bytes()
            result = parser.parse(xml_bytes)
            
            print(f"✅ Parseado exitosamente")
            print(f"   ID Externo: {result['external_id']}")
            print(f"   Fecha: {result['issue_date']}")
            print(f"   Proveedor: {result['supplier']['name']}")
            print(f"   NIT Proveedor: {result['supplier']['tax_id']}")
            print(f"   Cliente: {result['customer']['name']}")
            print(f"   NIT Cliente: {result['customer']['tax_id']}")
            print(f"   Total: {result['currency']} {result['total_amount']}")
            print(f"   Impuestos: {result['tax_amount']}")
            print(f"   Líneas: {len(result['lines'])}")
            
            for i, line in enumerate(result['lines'][:3], 1):
                print(f"      Línea {i}: {line.description} - Cantidad: {line.quantity} - Total: {line.line_extension_amount}")
            
        except Exception as e:
            print(f"❌ Error al parsear: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_all_formats()
