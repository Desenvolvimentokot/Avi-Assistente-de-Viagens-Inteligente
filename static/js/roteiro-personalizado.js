/**
 * Roteiro Personalizado - Core JavaScript
 * 
 * Este arquivo gerencia todas as interações do painel de roteiro personalizado,
 * incluindo:
 * - Sincronização entre chat e roteiro
 * - Adição/remoção de blocos de conteúdo
 * - Responsividade e navegação entre painéis
 * - Interações com o modal de mapa
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando Roteiro Personalizado');
    
    // Elementos do DOM
    const chatPanel = document.getElementById('chatPanel');
    const roteiroPanel = document.getElementById('roteiroPanel');
    const toggleChatBtn = document.getElementById('toggleChatBtn');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const dayTabs = document.getElementById('dayTabs');
    const dayBlocks = document.getElementById('dayBlocks');
    const btnAddManually = document.getElementById('btnAddManually');
    const btnSaveRoteiro = document.getElementById('btnSaveRoteiro');
    const btnShareRoteiro = document.getElementById('btnShareRoteiro');
    const btnExportPDF = document.getElementById('btnExportPDF');
    const editDestinationBtn = document.getElementById('editDestinationBtn');
    const saveDestinationBtn = document.getElementById('saveDestinationBtn');
    const saveItemBtn = document.getElementById('saveItemBtn');
    
    // Destino e datas
    const destinationTitle = document.getElementById('destinationTitle');
    const destinationDates = document.getElementById('destinationDates');
    const destinationDetail = document.getElementById('destinationDetail');
    const durationDetail = document.getElementById('durationDetail');
    const travelersDetail = document.getElementById('travelersDetail');
    
    // Modais
    const editDestinationModal = new bootstrap.Modal(document.getElementById('editDestinationModal'));
    const addItemModal = new bootstrap.Modal(document.getElementById('addItemModal'));
    const mapModal = new bootstrap.Modal(document.getElementById('mapModal'));
    
    // Estado atual do roteiro
    let currentRoteiro = {
        id: null,
        destination: '',
        startDate: null,
        endDate: null,
        travelers: 1,
        days: []
    };
    
    // Dia ativo no momento
    let activeDayIndex = 0;
    
    // ========================================
    // Inicialização
    // ========================================
    
    // Verificar se há um roteiro salvo em cookie
    checkExistingRoteiro();
    
    // Expandir textarea quando o usuário digita
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Enviar mensagem quando clicar no botão ou pressionar Enter
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Alternar painel de chat (colapsar/expandir)
    toggleChatBtn.addEventListener('click', function() {
        chatPanel.classList.toggle('collapsed');
        const icon = this.querySelector('i');
        
        if (chatPanel.classList.contains('collapsed')) {
            icon.classList.remove('fa-chevron-left');
            icon.classList.add('fa-chevron-right');
        } else {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-left');
        }
    });
    
    // Botão para editar informações de destino
    editDestinationBtn.addEventListener('click', function() {
        document.getElementById('editDestination').value = currentRoteiro.destination;
        document.getElementById('editStartDate').value = currentRoteiro.startDate;
        document.getElementById('editEndDate').value = currentRoteiro.endDate;
        document.getElementById('editTravelers').value = currentRoteiro.travelers;
        
        editDestinationModal.show();
    });
    
    // Salvar alterações de destino
    saveDestinationBtn.addEventListener('click', function() {
        const destination = document.getElementById('editDestination').value;
        const startDate = document.getElementById('editStartDate').value;
        const endDate = document.getElementById('editEndDate').value;
        const travelers = parseInt(document.getElementById('editTravelers').value) || 1;
        
        // Atualizar estado do roteiro
        currentRoteiro.destination = destination;
        currentRoteiro.startDate = startDate;
        currentRoteiro.endDate = endDate;
        currentRoteiro.travelers = travelers;
        
        // Reconstruir dias com base nas novas datas
        createDaysFromDates();
        
        // Atualizar UI
        updateRoteiroUI();
        
        // Fechar modal
        editDestinationModal.hide();
        
        // Salvar no servidor ou cookie
        updateRoteiroOnServer();
    });
    
    // Botão para adicionar item manualmente
    btnAddManually.addEventListener('click', function() {
        // Preencher os selects de dias
        const daySelects = [
            document.getElementById('flightDay'),
            document.getElementById('hotelDay'),
            document.getElementById('activityDay'),
            document.getElementById('noteDay')
        ];
        
        daySelects.forEach(select => {
            select.innerHTML = '';
            currentRoteiro.days.forEach((day, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `Dia ${index + 1} - ${formatDate(day.date)}`;
                select.appendChild(option);
            });
            
            // Selecionar o dia ativo
            if (select.options.length > activeDayIndex) {
                select.selectedIndex = activeDayIndex;
            }
        });
        
        addItemModal.show();
    });
    
    // Salvar item ao roteiro
    saveItemBtn.addEventListener('click', function() {
        // Determinar qual tab está ativa
        const activeTabId = document.querySelector('#itemTypeTabs .nav-link.active').id;
        
        let newBlock = {
            id: `block_${Date.now()}`,
            type: '',
            title: ''
        };
        
        // Obter dados do formulário e criar o bloco apropriado
        switch (activeTabId) {
            case 'flight-tab':
                const flightAirline = document.getElementById('flightAirline').value;
                const flightNumber = document.getElementById('flightNumber').value;
                const flightOrigin = document.getElementById('flightOrigin').value;
                const flightDestination = document.getElementById('flightDestination').value;
                const flightDepartureTime = document.getElementById('flightDepartureTime').value;
                const flightArrivalTime = document.getElementById('flightArrivalTime').value;
                const flightPrice = document.getElementById('flightPrice').value;
                const flightDay = parseInt(document.getElementById('flightDay').value);
                
                newBlock.type = 'flight';
                newBlock.title = `Voo ${flightAirline} ${flightNumber}`;
                newBlock.airline = flightAirline;
                newBlock.flightNumber = flightNumber;
                newBlock.departureAirport = flightOrigin;
                newBlock.arrivalAirport = flightDestination;
                newBlock.departureTime = flightDepartureTime;
                newBlock.arrivalTime = flightArrivalTime;
                newBlock.price = parseFloat(flightPrice) || 0;
                
                // Adicionar ao dia selecionado
                addBlockToDay(newBlock, flightDay);
                break;
                
            case 'hotel-tab':
                const hotelName = document.getElementById('hotelName').value;
                const hotelStars = document.getElementById('hotelStars').value;
                const hotelAddress = document.getElementById('hotelAddress').value;
                const hotelCheckIn = document.getElementById('hotelCheckIn').value;
                const hotelCheckOut = document.getElementById('hotelCheckOut').value;
                const hotelPrice = document.getElementById('hotelPrice').value;
                const hotelDay = parseInt(document.getElementById('hotelDay').value);
                
                newBlock.type = 'hotel';
                newBlock.title = hotelName;
                newBlock.name = hotelName;
                newBlock.location = hotelAddress;
                newBlock.stars = parseInt(hotelStars) || 3;
                newBlock.checkIn = hotelCheckIn;
                newBlock.checkOut = hotelCheckOut;
                newBlock.pricePerNight = parseFloat(hotelPrice) || 0;
                
                // Adicionar ao dia selecionado
                addBlockToDay(newBlock, hotelDay);
                break;
                
            case 'activity-tab':
                const activityName = document.getElementById('activityName').value;
                const activityLocation = document.getElementById('activityLocation').value;
                const activityDate = document.getElementById('activityDate').value;
                const activityTime = document.getElementById('activityTime').value;
                const activityPrice = document.getElementById('activityPrice').value;
                const activityNotes = document.getElementById('activityNotes').value;
                const activityDay = parseInt(document.getElementById('activityDay').value);
                
                newBlock.type = 'activity';
                newBlock.title = activityName;
                newBlock.name = activityName;
                newBlock.location = activityLocation;
                newBlock.datetime = activityDate && activityTime ? `${activityDate}T${activityTime}` : null;
                newBlock.price = parseFloat(activityPrice) || 0;
                newBlock.notes = activityNotes;
                
                // Adicionar ao dia selecionado
                addBlockToDay(newBlock, activityDay);
                break;
                
            case 'note-tab':
                const noteTitle = document.getElementById('noteTitle').value;
                const noteContent = document.getElementById('noteContent').value;
                const noteDay = parseInt(document.getElementById('noteDay').value);
                
                newBlock.type = 'note';
                newBlock.title = noteTitle;
                newBlock.content = noteContent;
                
                // Adicionar ao dia selecionado
                addBlockToDay(newBlock, noteDay);
                break;
        }
        
        // Limpar formulários
        document.getElementById('flightForm').reset();
        document.getElementById('hotelForm').reset();
        document.getElementById('activityForm').reset();
        document.getElementById('noteForm').reset();
        
        // Fechar modal
        addItemModal.hide();
        
        // Atualizar UI para mostrar o dia com o novo item
        showDay(newBlock.type === 'flight' ? parseInt(document.getElementById('flightDay').value) : 
                newBlock.type === 'hotel' ? parseInt(document.getElementById('hotelDay').value) : 
                newBlock.type === 'activity' ? parseInt(document.getElementById('activityDay').value) : 
                parseInt(document.getElementById('noteDay').value));
        
        // Salvar no servidor ou cookie
        updateRoteiroOnServer();
    });
    
    // Salvar roteiro completo
    btnSaveRoteiro.addEventListener('click', function() {
        updateRoteiroOnServer();
        
        // Feedback visual
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-check"></i> Salvo';
        
        setTimeout(() => {
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save"></i> Salvar';
        }, 2000);
    });
    
    // ========================================
    // Funções auxiliares
    // ========================================
    
    // Função para obter cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Função para definir cookie
    function setCookie(name, value, days = 30) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/`;
    }
    
    // Verificar se já existe um roteiro
    function checkExistingRoteiro() {
        // Verificar primeiro se há um ID de roteiro em cookie
        const roteiroId = getCookie('roteiro_atual_id');
        
        if (roteiroId) {
            // Temos um ID salvo, carregar do servidor
            loadRoteiro(roteiroId);
        } else {
            // Ver se há dados de roteiro no cookie (método alternativo)
            const roteiroData = getCookie('roteiro_data');
            
            if (roteiroData) {
                try {
                    const parsedData = JSON.parse(roteiroData);
                    // Inicializar com dados do cookie
                    updateRoteiroState(parsedData);
                } catch (e) {
                    console.error('Erro ao processar dados do roteiro:', e);
                    // Inicializar um roteiro novo
                    createDaysFromDates();
                }
            } else {
                // Inicializar um roteiro novo
                createDaysFromDates();
            }
        }
        
        // Verificar se há voos selecionados no cookie
        const selectedFlights = getCookie('roteiro_selected_flights');
        if (selectedFlights) {
            try {
                const flights = JSON.parse(selectedFlights);
                console.log('Voos selecionados encontrados:', flights);
                
                // Adicionar voos ao roteiro
                flights.forEach(flight => {
                    // Converter para o formato de bloco do roteiro
                    const flightBlock = convertFlightToBlock(flight);
                    
                    // Se já temos dias no roteiro, adicionar ao primeiro dia
                    if (currentRoteiro.days.length > 0) {
                        // Se não tem blocks, criar array
                        if (!currentRoteiro.days[0].blocks) {
                            currentRoteiro.days[0].blocks = [];
                        }
                        
                        // Adicionar ao primeiro dia
                        currentRoteiro.days[0].blocks.push(flightBlock);
                    }
                });
                
                // Atualizar UI
                updateRoteiroUI();
                
                // Limpar cookie de voos selecionados para evitar duplicação
                setCookie('roteiro_selected_flights', '', -1);
            } catch (e) {
                console.error('Erro ao processar voos selecionados:', e);
            }
        }
    }
    
    // Converter voo da API Amadeus para formato de bloco
    function convertFlightToBlock(flight) {
        // Extrair dados básicos do primeiro segmento de ida
        const outboundSegments = flight.itineraries[0].segments;
        const firstSegment = outboundSegments[0];
        const lastSegment = outboundSegments[outboundSegments.length - 1];
        
        const departureDateTime = firstSegment.departure.at;
        const arrivalDateTime = lastSegment.arrival.at;
        const departureAirport = firstSegment.departure.iataCode;
        const arrivalAirport = lastSegment.arrival.iataCode;
        const airline = firstSegment.carrierCode;
        const flightNumber = firstSegment.number;
        const price = parseFloat(flight.price.total);
        
        return {
            id: `flight_${flight.id}`,
            type: 'flight',
            title: `Voo ${airline} ${flightNumber}`,
            airline: airline,
            flightNumber: flightNumber,
            departureAirport: departureAirport,
            arrivalAirport: arrivalAirport,
            departureTime: departureDateTime,
            arrivalTime: arrivalDateTime,
            price: price,
            currency: flight.price.currency || 'BRL',
            segments: outboundSegments.map(segment => ({
                departureAirport: segment.departure.iataCode,
                arrivalAirport: segment.arrival.iataCode,
                departureTime: segment.departure.at,
                arrivalTime: segment.arrival.at,
                airline: segment.carrierCode,
                flightNumber: segment.number
            }))
        };
    }
    
    // Carregar roteiro do servidor
    function loadRoteiro(roteiroId) {
        console.log(`Carregando roteiro ${roteiroId}...`);
        
        // Fazer requisição para a API
        fetch(`/api/roteiro/obter?id=${roteiroId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Roteiro carregado com sucesso:', data.roteiro);
                    updateRoteiroState(data.roteiro);
                } else {
                    console.error('Erro ao carregar roteiro:', data.error);
                    // Inicializar um roteiro novo
                    createDaysFromDates();
                }
            })
            .catch(error => {
                console.error('Erro ao carregar roteiro:', error);
                // Inicializar um roteiro novo
                createDaysFromDates();
            });
    }
    
    // Atualizar estado do roteiro
    function updateRoteiroState(novoRoteiro) {
        // Transferir propriedades
        currentRoteiro.id = novoRoteiro.id || null;
        currentRoteiro.destination = novoRoteiro.destination || 'Sem destino';
        currentRoteiro.startDate = novoRoteiro.startDate || null;
        currentRoteiro.endDate = novoRoteiro.endDate || null;
        currentRoteiro.travelers = novoRoteiro.travelers || 1;
        
        // Se as datas foram fornecidas
        if (currentRoteiro.startDate) {
            // Se já temos dias, usar eles
            if (novoRoteiro.days && novoRoteiro.days.length > 0) {
                currentRoteiro.days = novoRoteiro.days;
            } else {
                // Senão, criar dias com base nas datas
                createDaysFromDates();
            }
        } else {
            // Sem datas, usar dias existentes ou criar um dia vazio
            currentRoteiro.days = novoRoteiro.days || [{ date: null, title: 'Dia 1', blocks: [] }];
        }
        
        // Atualizar UI
        updateRoteiroUI();
    }
    
    // Criar dias a partir das datas de início e fim
    function createDaysFromDates() {
        // Se não temos data de início, criar um dia genérico
        if (!currentRoteiro.startDate) {
            currentRoteiro.days = [{ date: null, title: 'Dia 1', blocks: [] }];
            return;
        }
        
        // Calcular duração da viagem
        const start = new Date(currentRoteiro.startDate);
        const end = currentRoteiro.endDate ? new Date(currentRoteiro.endDate) : new Date(start);
        
        // Garantir que end não seja antes de start
        if (end < start) {
            end.setTime(start.getTime());
            currentRoteiro.endDate = currentRoteiro.startDate;
        }
        
        // Calcular número de dias
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1 para incluir o último dia
        
        // Criar array de dias
        const days = [];
        
        for (let i = 0; i < diffDays; i++) {
            const date = new Date(start);
            date.setDate(start.getDate() + i);
            
            // Construir título do dia
            const dayTitle = i === 0 ? 'Dia 1 (Chegada)' : 
                             i === diffDays - 1 ? `Dia ${i + 1} (Partida)` : 
                             `Dia ${i + 1}`;
            
            // Preservar blocos se o dia já existia
            const existingDay = currentRoteiro.days.find(d => {
                if (!d.date) return false;
                const dDate = new Date(d.date);
                return dDate.toDateString() === date.toDateString();
            });
            
            days.push({
                date: date.toISOString().split('T')[0],
                title: dayTitle,
                blocks: existingDay ? existingDay.blocks : []
            });
        }
        
        // Atualizar dias do roteiro
        currentRoteiro.days = days;
    }
    
    // Atualizar interface do roteiro
    function updateRoteiroUI() {
        // Atualizar título e informações de destino
        destinationTitle.textContent = currentRoteiro.destination || 'Planeje sua viagem';
        
        // Formatar datas
        if (currentRoteiro.startDate && currentRoteiro.endDate) {
            const startFormatted = formatDate(currentRoteiro.startDate);
            const endFormatted = formatDate(currentRoteiro.endDate);
            destinationDates.textContent = `${startFormatted} a ${endFormatted}`;
            
            // Calcular duração
            const start = new Date(currentRoteiro.startDate);
            const end = new Date(currentRoteiro.endDate);
            const diffTime = Math.abs(end - start);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
            durationDetail.textContent = `${diffDays} dias`;
        } else if (currentRoteiro.startDate) {
            destinationDates.textContent = formatDate(currentRoteiro.startDate);
            durationDetail.textContent = '1 dia';
        } else {
            destinationDates.textContent = 'Escolha as datas da sua viagem';
            durationDetail.textContent = '...';
        }
        
        // Detalhes adicionais
        destinationDetail.textContent = currentRoteiro.destination || '...';
        travelersDetail.textContent = `${currentRoteiro.travelers} viajante${currentRoteiro.travelers > 1 ? 's' : ''}`;
        
        // Renderizar navegação de dias
        renderDays();
        
        // Mostrar o dia atual
        showDay(activeDayIndex);
    }
    
    // Renderizar navegador de dias
    function renderDays() {
        dayTabs.innerHTML = '';
        
        currentRoteiro.days.forEach((day, index) => {
            const dayElement = createDayElement(day, index);
            dayTabs.appendChild(dayElement);
        });
    }
    
    // Criar elemento de aba para um dia
    function createDayElement(day, index) {
        const button = document.createElement('button');
        button.className = `day-tab ${index === activeDayIndex ? 'active' : ''}`;
        button.textContent = day.title || `Dia ${index + 1}`;
        button.setAttribute('data-day-index', index);
        
        button.addEventListener('click', function() {
            // Atualizar dia ativo
            showDay(index);
        });
        
        return button;
    }
    
    // Mostrar conteúdo de um dia específico
    function showDay(dayIndex) {
        // Verificar se o índice é válido
        if (dayIndex < 0 || dayIndex >= currentRoteiro.days.length) {
            console.error(`Índice de dia inválido: ${dayIndex}`);
            return;
        }
        
        // Atualizar índice ativo
        activeDayIndex = dayIndex;
        
        // Atualizar classes nas abas
        const tabs = dayTabs.querySelectorAll('.day-tab');
        tabs.forEach(tab => {
            const index = parseInt(tab.getAttribute('data-day-index'));
            if (index === activeDayIndex) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        // Obter o dia atual
        const currentDay = currentRoteiro.days[activeDayIndex];
        
        // Limpar conteúdo anterior
        dayBlocks.innerHTML = '';
        
        // Se não há blocos ou está vazio, mostrar estado vazio
        if (!currentDay.blocks || currentDay.blocks.length === 0) {
            dayBlocks.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-suitcase-rolling"></i>
                    </div>
                    <h4>Dia sem atividades</h4>
                    <p>Adicione voos, hospedagens ou atividades para este dia.</p>
                    <button class="btn btn-primary btn-add-item" id="btnAddItemDay">
                        <i class="fas fa-plus"></i> Adicionar Item
                    </button>
                </div>
            `;
            
            // Adicionar listener ao botão
            document.getElementById('btnAddItemDay').addEventListener('click', function() {
                btnAddManually.click();
            });
            
            return;
        }
        
        // Renderizar cada bloco do dia
        currentDay.blocks.forEach(block => {
            const blockElement = document.createElement('div');
            blockElement.className = `block block-${block.type}`;
            blockElement.setAttribute('data-block-id', block.id);
            
            // HTML específico por tipo de bloco
            blockElement.innerHTML = createBlockHTML(block);
            
            // Adicionar ao container
            dayBlocks.appendChild(blockElement);
            
            // Adicionar listeners
            setupBlockListeners(blockElement, block);
        });
    }
    
    // Criar HTML para um bloco
    function createBlockHTML(block) {
        // Header comum para todos os tipos
        let blockIcon = '';
        switch (block.type) {
            case 'flight':
                blockIcon = '<i class="fas fa-plane"></i>';
                break;
            case 'hotel':
                blockIcon = '<i class="fas fa-hotel"></i>';
                break;
            case 'activity':
                blockIcon = '<i class="fas fa-hiking"></i>';
                break;
            case 'note':
                blockIcon = '<i class="fas fa-sticky-note"></i>';
                break;
        }
        
        let headerHTML = `
            <div class="block-header">
                <div class="block-title">
                    ${blockIcon} ${block.title || 'Item sem título'}
                </div>
                <div class="block-actions">
                    <button class="block-action-btn btn-expand" title="Expandir/Retrair">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                    <button class="block-action-btn btn-location" title="Ver no mapa">
                        <i class="fas fa-map-marker-alt"></i>
                    </button>
                    <button class="block-action-btn btn-remove" title="Remover">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Conteúdo específico por tipo
        let contentHTML = `
            <div class="block-content">
                ${createBlockContent(block)}
            </div>
        `;
        
        return headerHTML + contentHTML;
    }
    
    // Criar conteúdo específico para cada tipo de bloco
    function createBlockContent(block) {
        switch (block.type) {
            case 'flight':
                // Formatar horários
                const departureTime = block.departureTime ? new Date(block.departureTime) : null;
                const arrivalTime = block.arrivalTime ? new Date(block.arrivalTime) : null;
                
                // Calcular duração
                let duration = '';
                if (departureTime && arrivalTime) {
                    const diffMs = arrivalTime - departureTime;
                    const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
                    const diffMins = Math.round((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                    duration = `${diffHrs}h ${diffMins}m`;
                }
                
                return `
                    <div class="flight-details">
                        <div class="flight-route">
                            <div class="route-airport">
                                <div class="airport-code">${block.departureAirport || '?'}</div>
                                <div class="airport-time">${departureTime ? departureTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}</div>
                            </div>
                            
                            <div class="route-divider">
                                <div class="route-line"></div>
                                <div class="route-duration">${duration || '?'}</div>
                            </div>
                            
                            <div class="route-airport">
                                <div class="airport-code">${block.arrivalAirport || '?'}</div>
                                <div class="airport-time">${arrivalTime ? arrivalTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}</div>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Companhia</div>
                            <div class="detail-value">${block.airline || 'Não especificada'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Voo</div>
                            <div class="detail-value">${block.flightNumber || 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Data</div>
                            <div class="detail-value">${departureTime ? departureTime.toLocaleDateString() : 'Não especificada'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Preço</div>
                            <div class="detail-price">${formatPrice(block.price, block.currency)}</div>
                        </div>
                    </div>
                `;
                
            case 'hotel':
                // Formatar datas
                const checkIn = block.checkIn ? new Date(block.checkIn) : null;
                const checkOut = block.checkOut ? new Date(block.checkOut) : null;
                
                // Calcular número de noites
                let nights = '';
                if (checkIn && checkOut) {
                    const diffTime = Math.abs(checkOut - checkIn);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    nights = `${diffDays} noite${diffDays > 1 ? 's' : ''}`;
                }
                
                // Criar estrelas
                let starsHTML = '';
                for (let i = 0; i < 5; i++) {
                    if (i < block.stars) {
                        starsHTML += '<i class="fas fa-star"></i>';
                    } else {
                        starsHTML += '<i class="far fa-star"></i>';
                    }
                }
                
                return `
                    <div class="hotel-details">
                        <div class="detail-group">
                            <div class="detail-label">Nome</div>
                            <div class="detail-value">${block.name || 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Classificação</div>
                            <div class="detail-value">${starsHTML}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Endereço</div>
                            <div class="detail-value">${block.location || 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Check-in</div>
                            <div class="detail-value">${checkIn ? checkIn.toLocaleDateString() : 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Check-out</div>
                            <div class="detail-value">${checkOut ? checkOut.toLocaleDateString() : 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Estadia</div>
                            <div class="detail-value">${nights || 'Não especificada'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Preço por noite</div>
                            <div class="detail-price">${formatPrice(block.pricePerNight, block.currency)}</div>
                        </div>
                    </div>
                `;
                
            case 'activity':
                // Formatar data e hora
                const datetime = block.datetime ? new Date(block.datetime) : null;
                
                return `
                    <div class="activity-details">
                        <div class="detail-group">
                            <div class="detail-label">Atividade</div>
                            <div class="detail-value">${block.name || 'Não especificada'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Local</div>
                            <div class="detail-value">${block.location || 'Não especificado'}</div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Data e Hora</div>
                            <div class="detail-value">
                                ${datetime ? 
                                    `${datetime.toLocaleDateString()} às ${datetime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}` : 
                                    'Não especificado'}
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-label">Preço</div>
                            <div class="detail-price">${formatPrice(block.price, block.currency)}</div>
                        </div>
                        
                        ${block.notes ? `
                            <div class="detail-group" style="width: 100%;">
                                <div class="detail-label">Observações</div>
                                <div class="detail-value">${block.notes}</div>
                            </div>
                        ` : ''}
                    </div>
                `;
                
            case 'note':
                return `
                    <div class="note-details">
                        <div class="detail-group" style="width: 100%;">
                            <div class="detail-value">${block.content || 'Nota sem conteúdo'}</div>
                        </div>
                    </div>
                `;
                
            default:
                return `<div>Tipo de bloco não reconhecido</div>`;
        }
    }
    
    // Configurar listeners para um bloco
    function setupBlockListeners(blockElement, block) {
        // Botão expandir/retrair
        const expandBtn = blockElement.querySelector('.btn-expand');
        expandBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            blockElement.classList.toggle('expanded');
            
            // Atualizar ícone
            const icon = this.querySelector('i');
            if (blockElement.classList.contains('expanded')) {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
        
        // Expandir/retrair quando clicar no header
        const header = blockElement.querySelector('.block-header');
        header.addEventListener('click', function(e) {
            // Evitar expandir se clicar em um botão de ação
            if (e.target.closest('.block-actions')) return;
            
            // Simular clique no botão de expandir
            expandBtn.click();
        });
        
        // Botão de localização
        const locationBtn = blockElement.querySelector('.btn-location');
        locationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Obter localização com base no tipo de bloco
            let location = '';
            switch (block.type) {
                case 'flight':
                    location = block.arrivalAirport || '';
                    break;
                case 'hotel':
                    location = block.location || '';
                    break;
                case 'activity':
                    location = block.location || '';
                    break;
                default:
                    // Não aplicável para notas
                    return;
            }
            
            // Se não tem localização, não mostrar mapa
            if (!location) {
                console.log('Localização não disponível para este item');
                return;
            }
            
            // Mostrar modal de mapa com a localização
            showMapModal(location);
        });
        
        // Botão remover
        const removeBtn = blockElement.querySelector('.btn-remove');
        removeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Confirmar remoção
            if (confirm(`Deseja remover este item do roteiro?`)) {
                removeBlockFromRoteiro(block.id, activeDayIndex);
            }
        });
    }
    
    // Adicionar bloco a um dia específico
    function addBlockToDay(block, dayIndex) {
        // Verificar se o índice é válido
        if (dayIndex < 0 || dayIndex >= currentRoteiro.days.length) {
            console.error(`Índice de dia inválido: ${dayIndex}`);
            return;
        }
        
        // Garantir que o dia tenha um array de blocos
        if (!currentRoteiro.days[dayIndex].blocks) {
            currentRoteiro.days[dayIndex].blocks = [];
        }
        
        // Adicionar bloco ao dia
        currentRoteiro.days[dayIndex].blocks.push(block);
        
        // Notificar o chat sobre o novo item
        notifyChatAboutNewBlock(block, dayIndex);
    }
    
    // Remover bloco do roteiro
    function removeBlockFromRoteiro(blockId, dayIndex) {
        // Verificar se o índice é válido
        if (dayIndex < 0 || dayIndex >= currentRoteiro.days.length) {
            console.error(`Índice de dia inválido: ${dayIndex}`);
            return;
        }
        
        const day = currentRoteiro.days[dayIndex];
        
        // Verificar se o dia tem blocos
        if (!day.blocks || day.blocks.length === 0) {
            console.error(`Dia ${dayIndex} não tem blocos`);
            return;
        }
        
        // Encontrar índice do bloco
        const blockIndex = day.blocks.findIndex(b => b.id === blockId);
        
        if (blockIndex === -1) {
            console.error(`Bloco ${blockId} não encontrado no dia ${dayIndex}`);
            return;
        }
        
        // Remover bloco
        const removedBlock = day.blocks.splice(blockIndex, 1)[0];
        
        // Atualizar UI
        showDay(dayIndex);
        
        // Notificar o chat sobre a remoção
        notifyChatAboutRemovedBlock(removedBlock);
        
        // Salvar no servidor ou cookie
        updateRoteiroOnServer();
    }
    
    // Mostrar modal de mapa
    function showMapModal(location) {
        // Atualizar título do modal
        document.getElementById('mapModalLabel').textContent = `Mapa - ${location}`;
        
        // Mostrar modal
        mapModal.show();
        
        // Inicializar o mapa após o modal estar visível
        setTimeout(() => {
            initMap(location);
        }, 500);
    }
    
    // Inicializar mapa com Leaflet
    function initMap(location) {
        // Limpar container
        const mapContainer = document.getElementById('mapContainer');
        mapContainer.innerHTML = '';
        
        // Criar mapa
        const map = L.map('mapContainer').setView([0, 0], 13);
        
        // Adicionar camada de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Usar geocodificação para obter coordenadas
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location)}`)
            .then(response => response.json())
            .then(data => {
                if (data && data.length > 0) {
                    const lat = parseFloat(data[0].lat);
                    const lon = parseFloat(data[0].lon);
                    
                    // Atualizar visão do mapa
                    map.setView([lat, lon], 13);
                    
                    // Adicionar marcador
                    L.marker([lat, lon]).addTo(map)
                        .bindPopup(location)
                        .openPopup();
                } else {
                    mapContainer.innerHTML = `
                        <div class="alert alert-warning">
                            Não foi possível encontrar coordenadas para "${location}".
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Erro ao buscar coordenadas:', error);
                mapContainer.innerHTML = `
                    <div class="alert alert-danger">
                        Erro ao carregar o mapa: ${error.message}
                    </div>
                `;
            });
    }
    
    // Enviar mensagem para o chat
    function sendMessage() {
        const message = userInput.value.trim();
        
        if (!message) return;
        
        // Adicionar mensagem do usuário
        addMessageToChat(message, true);
        
        // Limpar input
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Processar mensagem (simulado - em produção enviaria para o backend)
        simulateAviResponse(message);
    }
    
    // Adicionar mensagem ao chat
    function addMessageToChat(content, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isUser ? 'user-message' : 'avi-message'}`;
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        
        // Scroll para a última mensagem
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Simular resposta da AVI (para demonstração)
    function simulateAviResponse(userMessage) {
        // Mostrar indicador de digitação
        const typingElement = document.createElement('div');
        typingElement.className = 'message avi-message typing';
        typingElement.innerHTML = '<div class="message-content"><p>AVI está digitando...</p></div>';
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Simular tempo de resposta
        setTimeout(() => {
            // Remover indicador de digitação
            chatMessages.removeChild(typingElement);
            
            // Resposta simulada baseada em palavras-chave
            let response = '';
            
            const lowerMessage = userMessage.toLowerCase();
            
            if (lowerMessage.includes('olá') || lowerMessage.includes('oi') || lowerMessage.includes('bom dia') || lowerMessage.includes('boa tarde') || lowerMessage.includes('boa noite')) {
                response = 'Olá! Como posso ajudar com o planejamento da sua viagem?';
            } else if (lowerMessage.includes('destino') || lowerMessage.includes('para onde')) {
                response = `Vejo que estamos planejando uma viagem para ${currentRoteiro.destination || 'um destino ainda não definido'}. Posso ajudar com sugestões de atrações, hotéis ou transportes?`;
            } else if (lowerMessage.includes('voo') || lowerMessage.includes('passagem') || lowerMessage.includes('avião')) {
                response = 'Para buscar voos, precisamos de algumas informações: origem, destino, datas e número de passageiros. Você pode me fornecer esses detalhes?';
            } else if (lowerMessage.includes('hotel') || lowerMessage.includes('hospedagem') || lowerMessage.includes('onde ficar')) {
                response = 'Posso ajudar a encontrar hotéis que se encaixem no seu orçamento e preferências. Você prefere ficar no centro da cidade ou em alguma região específica?';
            } else if (lowerMessage.includes('o que fazer') || lowerMessage.includes('atração') || lowerMessage.includes('passeio') || lowerMessage.includes('visitar')) {
                response = `${currentRoteiro.destination || 'Este destino'} tem muitas atrações interessantes! Você prefere atividades culturais, ao ar livre, ou experiências gastronômicas?`;
            } else if (lowerMessage.includes('orçamento') || lowerMessage.includes('preço') || lowerMessage.includes('custo') || lowerMessage.includes('caro')) {
                response = 'Posso ajudar a planejar sua viagem de acordo com seu orçamento. Quanto você planeja gastar nesta viagem aproximadamente?';
            } else if (lowerMessage.includes('obrigado') || lowerMessage.includes('obrigada') || lowerMessage.includes('valeu')) {
                response = 'Por nada! Estou aqui para ajudar a planejar a melhor viagem possível. Se tiver mais perguntas, é só me chamar!';
            } else if (lowerMessage.includes('roteiro') || lowerMessage.includes('itinerário') || lowerMessage.includes('plano')) {
                response = 'Estou ajudando a montar seu roteiro personalizado. Você pode ver e editar os itens no painel à direita. Gostaria de alguma sugestão específica para adicionar ao plano?';
            } else {
                response = 'Entendi. Como posso ajudar mais com o planejamento da sua viagem? Posso buscar voos, sugerir hospedagens ou recomendar atrações.';
            }
            
            // Adicionar resposta
            addMessageToChat(response);
        }, 1500);
    }
    
    // Notificar o chat sobre novo bloco adicionado
    function notifyChatAboutNewBlock(block, dayIndex) {
        const dayNumber = dayIndex + 1;
        let message = '';
        
        switch (block.type) {
            case 'flight':
                message = `✅ Adicionei o voo ${block.airline} ${block.flightNumber} de ${block.departureAirport} para ${block.arrivalAirport} ao Dia ${dayNumber} do seu roteiro.`;
                break;
            case 'hotel':
                message = `✅ Adicionei a hospedagem no ${block.name} ao Dia ${dayNumber} do seu roteiro.`;
                break;
            case 'activity':
                message = `✅ Adicionei a atividade "${block.name}" ao Dia ${dayNumber} do seu roteiro.`;
                break;
            case 'note':
                message = `✅ Adicionei uma nota sobre "${block.title}" ao Dia ${dayNumber} do seu roteiro.`;
                break;
        }
        
        if (message) {
            addMessageToChat(message);
        }
    }
    
    // Notificar o chat sobre bloco removido
    function notifyChatAboutRemovedBlock(block) {
        let message = '';
        
        switch (block.type) {
            case 'flight':
                message = `🗑️ Removi o voo ${block.airline} ${block.flightNumber} do seu roteiro.`;
                break;
            case 'hotel':
                message = `🗑️ Removi a hospedagem no ${block.name} do seu roteiro.`;
                break;
            case 'activity':
                message = `🗑️ Removi a atividade "${block.name}" do seu roteiro.`;
                break;
            case 'note':
                message = `🗑️ Removi a nota sobre "${block.title}" do seu roteiro.`;
                break;
        }
        
        if (message) {
            addMessageToChat(message);
        }
    }
    
    // Salvar roteiro no servidor
    function updateRoteiroOnServer() {
        console.log('Salvando roteiro...');
        
        // Se temos um ID, atualizar roteiro existente
        if (currentRoteiro.id) {
            fetch('/api/roteiro/atualizar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentRoteiro)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Roteiro atualizado com sucesso');
                } else {
                    console.error('Erro ao atualizar roteiro:', data.error);
                }
            })
            .catch(error => {
                console.error('Erro ao atualizar roteiro:', error);
            });
        } else {
            // Senão, criar novo roteiro
            fetch('/api/roteiro/salvar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentRoteiro)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Roteiro salvo com sucesso');
                    // Atualizar ID
                    currentRoteiro.id = data.roteiro_id;
                } else {
                    console.error('Erro ao salvar roteiro:', data.error);
                }
            })
            .catch(error => {
                console.error('Erro ao salvar roteiro:', error);
            });
        }
        
        // Salvar também em cookie (como fallback)
        setCookie('roteiro_data', JSON.stringify(currentRoteiro));
    }
    
    // ========================================
    // Funções utilitárias
    // ========================================
    
    // Formatar data
    function formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
        return date.toLocaleDateString('pt-BR', options);
    }
    
    // Formatar preço
    function formatPrice(price, currency = 'BRL') {
        if (price === undefined || price === null) return 'Preço não disponível';
        
        const formatter = new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: currency || 'BRL'
        });
        
        return formatter.format(price);
    }
});