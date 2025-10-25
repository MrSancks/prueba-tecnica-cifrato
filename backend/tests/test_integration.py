"""
Test de integración completo: Parser + AI Suggestions + Excel Export
Valida el flujo completo desde XML hasta sugerencias PUC
"""

import os
from app.infrastructure.services.invoice_parser import UBLInvoiceParser
from app.infrastructure.services.ai import GeminiAISuggestionService
from app.domain.invoices import Invoice, InvoiceLine


def test_integration_flow():
    """
    Simula el flujo completo:
    1. Parsear un AttachedDocument (standard-invoice-2.xml)
    2. Crear objeto Invoice del dominio
    3. Generar sugerencias PUC con AI
    """
    
    print("\n" + "="*70)
    print("TEST DE INTEGRACIÓN COMPLETO")
    print("="*70)
    
    # 1. PARSEAR XML (AttachedDocument con factura embebida)
    print("\n📄 PASO 1: Parseando standard-invoice-2.xml (AttachedDocument)")
    print("-" * 70)
    
    parser = UBLInvoiceParser()
    xml_path = "app/assessment-files/standard-invoice-2.xml"
    
    with open(xml_path, "rb") as f:
        xml_bytes = f.read()
    
    parsed_data = parser.parse(xml_bytes)
    
    print(f"✅ XML parseado exitosamente")
    print(f"   Tipo: AttachedDocument → Invoice (embebida)")
    print(f"   ID: {parsed_data['external_id']}")
    print(f"   Proveedor: {parsed_data['supplier']['name']}")
    print(f"   NIT: {parsed_data['supplier']['tax_id']}")
    print(f"   Total: {parsed_data['currency']} {parsed_data['total_amount']}")
    print(f"   Productos: {len(parsed_data['lines'])}")
    
    # 2. CREAR OBJETO INVOICE DEL DOMINIO
    print(f"\n📦 PASO 2: Creando objeto Invoice del dominio")
    print("-" * 70)
    
    invoice = Invoice(
        id="test-invoice-001",
        user_id="test-user",
        external_id=parsed_data['external_id'],
        issue_date=parsed_data['issue_date'],
        supplier_name=parsed_data['supplier']['name'],
        supplier_tax_id=parsed_data['supplier']['tax_id'],
        customer_name=parsed_data['customer']['name'],
        customer_tax_id=parsed_data['customer']['tax_id'],
        currency=parsed_data['currency'],
        total_amount=parsed_data['total_amount'],
        tax_amount=parsed_data['tax_amount'],
        lines=parsed_data['lines'],
        raw_xml=parsed_data['raw_xml'],
    )
    
    print(f"✅ Invoice creada con {len(invoice.lines)} líneas")
    for i, line in enumerate(invoice.lines[:3], 1):
        print(f"   {i}. {line.description} - {line.quantity} x {line.unit_price}")
    if len(invoice.lines) > 3:
        print(f"   ... y {len(invoice.lines) - 3} más")
    
    # 3. GENERAR SUGERENCIAS PUC
    print(f"\n🤖 PASO 3: Generando sugerencias PUC con Gemini AI")
    print("-" * 70)
    
    # Verificar que existe la API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY no configurada. Saltando prueba de AI.")
        print("   Para probar AI, ejecutar:")
        print("   $env:GEMINI_API_KEY='tu-api-key'; python test_integration.py")
        return
    
    ai_service = GeminiAISuggestionService()
    
    try:
        suggestions = ai_service.generate_suggestions_for_invoice(invoice)
        
        print(f"✅ Sugerencias generadas: {len(suggestions)}")
        
        # Validar que las sugerencias usan códigos PUC de INGRESOS (clase 4)
        print(f"\n📊 VALIDACIÓN DE CÓDIGOS PUC:")
        print("-" * 70)
        
        all_valid = True
        for i, suggestion in enumerate(suggestions[:5], 1):
            code = suggestion.puc_code_4_digits
            is_income = code.startswith("4")
            status = "✅" if is_income else "❌"
            
            print(f"{status} Sugerencia {i}:")
            print(f"   Código PUC: {code}")
            print(f"   Nombre: {suggestion.puc_code_name}")
            print(f"   Clase: {'INGRESOS (correcto)' if is_income else 'ERROR - No es ingreso'}")
            
            if not is_income:
                all_valid = False
                print(f"   ⚠️  Razón: {suggestion.reasoning}")
        
        if len(suggestions) > 5:
            print(f"   ... y {len(suggestions) - 5} sugerencias más")
        
        print(f"\n" + "="*70)
        if all_valid:
            print("🎉 RESULTADO: ¡TODAS LAS SUGERENCIAS SON CORRECTAS!")
            print("   Todas usan códigos PUC de clase 4 (Ingresos)")
        else:
            print("❌ RESULTADO: Algunas sugerencias usan códigos incorrectos")
            print("   Se esperaban solo códigos clase 4 (Ingresos)")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error generando sugerencias: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_integration_flow()
