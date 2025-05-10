/**
 * Script para substituir a tag [BOTÃO_TRIP_COM] nas mensagens da AVI
 * por um botão real que abre a página com o widget do Trip.com
 */

(function() {
    // Observador para detectar novas mensagens da AVI
    const chatObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    // Verificar se é uma mensagem da AVI (bot)
                    if (node.classList && (node.classList.contains('message') || node.classList.contains('bot-message'))) {
                        processMessage(node);
                    }
                }
            }
        });
    });

    // Processa uma mensagem para encontrar a tag [BOTÃO_TRIP_COM]
    function processMessage(messageNode) {
        const content = messageNode.textContent || messageNode.innerText;
        
        // Verificar se a mensagem contém a tag [BOTÃO_TRIP_COM]
        if (content && content.includes('[BOTÃO_TRIP_COM]')) {
            console.log('Tag [BOTÃO_TRIP_COM] encontrada, substituindo por botão real');
            
            // Extrair dados de voo do bloco [DADOS_VIAGEM]
            const flightInfo = extractFlightInfo(messageNode);
            
            if (flightInfo) {
                // Substituir a tag pelo botão
                replaceTagWithButton(messageNode, flightInfo);
            } else {
                console.error('Dados de voo não encontrados na mensagem');
            }
        }
    }

    // Extrai informações de voo do bloco [DADOS_VIAGEM]
    function extractFlightInfo(messageNode) {
        const content = messageNode.innerHTML;
        
        // Verificar se há bloco de dados
        const regex = /\[DADOS_VIAGEM\]([\s\S]*?)\[\/DADOS_VIAGEM\]/;
        const match = content.match(regex);
        
        if (!match) {
            console.error('Bloco [DADOS_VIAGEM] não encontrado');
            return null;
        }
        
        // Extrair dados
        const dataBlock = match[1];
        
        // Extrair parâmetros individuais
        const originMatch = /Origem:.*?\((.*?)\)/.exec(dataBlock);
        const destMatch = /Destino:.*?\((.*?)\)/.exec(dataBlock);
        const depDateMatch = /Data_Ida: (\d{4}-\d{2}-\d{2})/.exec(dataBlock);
        const retDateMatch = /Data_Volta: (\d{4}-\d{2}-\d{2})/.exec(dataBlock);
        const passengersMatch = /Passageiros: (\d+)/.exec(dataBlock);
        
        // Montar objeto com os dados
        return {
            origin: originMatch ? originMatch[1] : null,
            destination: destMatch ? destMatch[1] : null,
            departure_date: depDateMatch ? depDateMatch[1] : null,
            return_date: retDateMatch ? retDateMatch[1] : null,
            adults: passengersMatch ? parseInt(passengersMatch[1]) : 1
        };
    }

    // Função para extrair código de cidade a partir do código de aeroporto
    function getCityCodeFromAirport(airportCode) {
        // Mapeamento básico de aeroportos para cidades
        const airportToCityMap = {
            'GRU': 'sao', // São Paulo
            'SDU': 'rio', // Rio de Janeiro - Santos Dumont
            'GIG': 'rio', // Rio de Janeiro - Galeão
            'BSB': 'bsb', // Brasília
            'SSA': 'ssa', // Salvador
            'FOR': 'for', // Fortaleza
            'POA': 'poa', // Porto Alegre
            'MCZ': 'mcz', // Maceió
            'REC': 'rec', // Recife
            'CWB': 'cwb', // Curitiba
            'BEL': 'bel', // Belém
            'VCP': 'sao', // Campinas (São Paulo)
            'CNF': 'bho', // Belo Horizonte - Confins
            'FLN': 'fln', // Florianópolis
            'NAT': 'nat', // Natal
            'MAO': 'mao', // Manaus
        };
        
        // Retorna o código da cidade ou o próprio código do aeroporto em minúsculas como fallback
        return airportToCityMap[airportCode] || airportCode.toLowerCase();
    }
    
    // Substitui a tag [BOTÃO_TRIP_COM] por um botão real
    function replaceTagWithButton(messageNode, flightInfo) {
        // HTML original
        const originalHTML = messageNode.innerHTML;
        
        // Extrair códigos de cidade
        const dcity = getCityCodeFromAirport(flightInfo.origin);
        const acity = getCityCodeFromAirport(flightInfo.destination);
        
        // Construir URL do Trip.com no formato correto
        const tripUrl = `https://br.trip.com/flights/showfarefirst?dcity=${dcity}&acity=${acity}&ddate=${flightInfo.departure_date}&dairport=${flightInfo.origin}${flightInfo.return_date ? '&rdate=' + flightInfo.return_date + '&triptype=rt' : '&triptype=ow'}&class=y&quantity=${flightInfo.adults || 1}&locale=pt-BR&curr=BRL`;
        
        console.log('URL do Trip.com gerada:', tripUrl);
        
        // Criar elemento do botão
        const buttonHTML = `
            <div class="trip-button-container" style="margin: 15px 0;">
                <a href="${tripUrl}" 
                   target="_blank" 
                   class="trip-search-button" 
                   style="display: inline-block; padding: 12px 24px; background-color: #2681ff; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; transition: background-color 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    <span style="margin-right: 8px;">Ver opções de voos</span>
                    <i class="fas fa-search" style="font-size: 14px;"></i>
                </a>
            </div>
        `;
        
        // Substituir a tag pelo botão
        const newHTML = originalHTML.replace('[BOTÃO_TRIP_COM]', buttonHTML);
        messageNode.innerHTML = newHTML;
        
        // Adicionar evento de clique para logging
        setTimeout(() => {
            const button = messageNode.querySelector('.trip-search-button');
            if (button) {
                button.addEventListener('click', function() {
                    console.log('Botão Trip.com clicado, abrindo pesquisa com parâmetros:', flightInfo);
                });
            }
        }, 100);
    }

    // Iniciar observação quando o DOM estiver pronto
    function initObserver() {
        // Verificar se estamos na página de chat
        const chatContainer = document.querySelector('.chat-messages') || document.querySelector('.chat-container');
        if (!chatContainer) {
            console.log('Container de chat não encontrado, pulando inicialização do observador');
            return;
        }
        
        // Aplicar às mensagens existentes
        const existingMessages = chatContainer.querySelectorAll('.message, .bot-message');
        existingMessages.forEach(function(message) {
            processMessage(message);
        });
        
        // Configurar MutationObserver para novas mensagens
        chatObserver.observe(chatContainer, {
            childList: true,
            subtree: true
        });
        
        console.log('Observador de mensagens da AVI inicializado');
    }

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initObserver);
    } else {
        initObserver();
    }
    
    console.log('Script de detecção de botão Trip.com carregado');
})();