"""Test completo de todos los archivos XML en assessment-files"""

import os
from app.infrastructure.services.invoice_parser import UBLInvoiceParser


def test_all_xml_files():
    parser = UBLInvoiceParser()
    xml_dir = "app/assessment-files"
    
    # Obtener todos los archivos XML
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith(".xml")]
    xml_files.sort()
    
    print(f"\n{'='*60}")
    print(f"Testeando {len(xml_files)} archivos XML")
    print('='*60)
    
    results = {"success": [], "failed": []}
    
    for xml_file in xml_files:
        filepath = os.path.join(xml_dir, xml_file)
        print(f"\n{'='*60}")
        print(f"📄 {xml_file}")
        print('='*60)
        
        try:
            with open(filepath, "rb") as f:
                xml_bytes = f.read()
            
            result = parser.parse(xml_bytes)
            
            print(f"✅ Parseado exitosamente")
            print(f"   ID: {result['external_id']}")
            print(f"   Fecha: {result['issue_date']}")
            print(f"   Proveedor: {result['supplier']['name']}")
            print(f"   NIT: {result['supplier']['tax_id']}")
            print(f"   Total: {result['currency']} {result['total_amount']}")
            print(f"   Impuestos: {result['tax_amount']}")
            print(f"   Productos: {len(result['lines'])}")
            
            results["success"].append(xml_file)
            
        except Exception as e:
            print(f"❌ Error al parsear: {e}")
            results["failed"].append(xml_file)
    
    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print('='*60)
    print(f"✅ Exitosos: {len(results['success'])}/{len(xml_files)}")
    print(f"❌ Fallidos: {len(results['failed'])}/{len(xml_files)}")
    
    if results["failed"]:
        print(f"\nArchivos fallidos:")
        for f in results["failed"]:
            print(f"  - {f}")
    else:
        print(f"\n🎉 ¡Todos los archivos parseados exitosamente!")


if __name__ == "__main__":
    test_all_xml_files()
