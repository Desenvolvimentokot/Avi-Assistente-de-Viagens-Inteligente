
import logging
import os
import json
from datetime import datetime
import tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from flask import url_for

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFService:
    """
    Serviço para gerar PDFs de planejamentos de viagem
    """
    
    @staticmethod
    def generate_basic_pdf(travel_plan, user=None):
        """
        Gera um PDF básico (versão gratuita) com o resumo do planejamento
        
        Parâmetros:
        - travel_plan: objeto com os dados do planejamento
        - user: objeto do usuário (opcional)
        
        Retorna:
        - Caminho do arquivo PDF gerado
        """
        try:
            # Criar arquivo temporário para o PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Configurar documento
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.blue
            ))
            styles.add(ParagraphStyle(
                name='Subtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=6,
                spaceAfter=6,
                textColor=colors.darkblue
            ))
            styles.add(ParagraphStyle(
                name='Body',
                parent=styles['Normal'],
                fontSize=12,
                spaceBefore=2,
                spaceAfter=2
            ))
            styles.add(ParagraphStyle(
                name='Bullet',
                parent=styles['Normal'],
                fontSize=12,
                leftIndent=20,
                bulletIndent=10,
                spaceBefore=2,
                spaceAfter=2
            ))
            
            # Conteúdo do documento
            content = []
            
            # Título
            content.append(Paragraph(f"Planejamento de Viagem: {travel_plan['destination']}", styles['Title']))
            content.append(Spacer(1, 0.25*inch))
            
            # Data de geração
            generation_date = datetime.now().strftime("%d/%m/%Y")
            content.append(Paragraph(f"Gerado em: {generation_date}", styles['Normal']))
            content.append(Spacer(1, 0.25*inch))
            
            # Informações gerais
            content.append(Paragraph("Informações Gerais", styles['Subtitle']))
            content.append(Paragraph(f"<b>Destino:</b> {travel_plan['destination']}", styles['Body']))
            
            if travel_plan.get('start_date'):
                start_date = datetime.strptime(travel_plan['start_date'], "%Y-%m-%d").strftime("%d/%m/%Y") if isinstance(travel_plan['start_date'], str) else travel_plan['start_date'].strftime("%d/%m/%Y")
                content.append(Paragraph(f"<b>Data de início:</b> {start_date}", styles['Body']))
            
            if travel_plan.get('end_date'):
                end_date = datetime.strptime(travel_plan['end_date'], "%Y-%m-%d").strftime("%d/%m/%Y") if isinstance(travel_plan['end_date'], str) else travel_plan['end_date'].strftime("%d/%m/%Y")
                content.append(Paragraph(f"<b>Data de término:</b> {end_date}", styles['Body']))
            
            content.append(Spacer(1, 0.25*inch))
            
            # Detalhes do plano
            if travel_plan.get('details'):
                content.append(Paragraph("Detalhes do Plano", styles['Subtitle']))
                content.append(Paragraph(travel_plan['details'], styles['Body']))
                content.append(Spacer(1, 0.25*inch))
            
            # Voos
            if travel_plan.get('flights') and len(travel_plan['flights']) > 0:
                content.append(Paragraph("Voos", styles['Subtitle']))
                
                for flight in travel_plan['flights']:
                    content.append(Paragraph(f"<b>{flight['airline']} {flight['flight_number']}</b>", styles['Body']))
                    content.append(Paragraph(f"De: {flight['departure_location']} - Para: {flight['arrival_location']}", styles['Body']))
                    
                    if flight.get('departure_time'):
                        departure_time = flight['departure_time'].split('T')[0] if 'T' in flight['departure_time'] else flight['departure_time']
                        content.append(Paragraph(f"Data/Hora de partida: {departure_time}", styles['Body']))
                    
                    if flight.get('arrival_time'):
                        arrival_time = flight['arrival_time'].split('T')[0] if 'T' in flight['arrival_time'] else flight['arrival_time']
                        content.append(Paragraph(f"Data/Hora de chegada: {arrival_time}", styles['Body']))
                    
                    content.append(Paragraph(f"Preço: {flight['price']} {flight['currency']}", styles['Body']))
                    content.append(Spacer(1, 0.1*inch))
                
                content.append(Spacer(1, 0.15*inch))
            
            # Acomodações
            if travel_plan.get('accommodations') and len(travel_plan['accommodations']) > 0:
                content.append(Paragraph("Acomodações", styles['Subtitle']))
                
                for acc in travel_plan['accommodations']:
                    content.append(Paragraph(f"<b>{acc['name']}</b>", styles['Body']))
                    content.append(Paragraph(f"Localização: {acc['location']}", styles['Body']))
                    
                    if acc.get('check_in') and acc.get('check_out'):
                        check_in = acc['check_in'].split('T')[0] if 'T' in acc['check_in'] else acc['check_in']
                        check_out = acc['check_out'].split('T')[0] if 'T' in acc['check_out'] else acc['check_out']
                        content.append(Paragraph(f"Check-in: {check_in} - Check-out: {check_out}", styles['Body']))
                    
                    if acc.get('stars'):
                        content.append(Paragraph(f"Classificação: {'★' * acc['stars']}", styles['Body']))
                    
                    content.append(Paragraph(f"Preço por noite: {acc['price_per_night']} {acc['currency']}", styles['Body']))
                    content.append(Spacer(1, 0.1*inch))
                
                content.append(Spacer(1, 0.15*inch))
            
            # Rodapé
            content.append(Spacer(1, 0.5*inch))
            content.append(Paragraph("Planejamento de viagem gerado pelo Flai - Seu assistente virtual de viagens", styles['Normal']))
            
            # Construir o documento
            doc.build(content)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Erro ao gerar PDF básico: {str(e)}")
            return None
    
    @staticmethod
    def generate_premium_pdf(travel_plan, user=None):
        """
        Gera um PDF premium com o resumo do planejamento
        
        Parâmetros:
        - travel_plan: objeto com os dados do planejamento
        - user: objeto do usuário (opcional)
        
        Retorna:
        - Caminho do arquivo PDF gerado
        """
        try:
            # Por enquanto, usar a mesma implementação do PDF básico
            # Em produção, seria integrado com a API da Gamma.ai
            return PDFService.generate_basic_pdf(travel_plan, user)
            
        except Exception as e:
            logger.error(f"Erro ao gerar PDF premium: {str(e)}")
            return None
            
    @staticmethod
    def delete_pdf(file_path):
        """
        Remove um arquivo PDF após uso
        
        Parâmetros:
        - file_path: caminho do arquivo a ser removido
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                return True
        except Exception as e:
            logger.error(f"Erro ao remover arquivo PDF: {str(e)}")
            return False
