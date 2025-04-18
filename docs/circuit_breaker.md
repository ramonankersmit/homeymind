# Circuit Breaker Implementatie

## Overzicht
De circuit breaker implementatie beschermt MQTT operaties tegen falen door:
- Automatisch retryen van tijdelijke fouten
- Blokkeren van operaties bij aanhoudende problemen
- Geleidelijk herstel via half-open state
- Uitgebreide monitoring en metrics

## Configuratie

```python
breaker = CircuitBreaker(
    name="mqtt_publish",
    max_delay=2.0,        # Maximale retry tijd in seconden
    max_retries=3,        # Aantal retries voor open state
    exceptions=(ConnectionError, TimeoutError),  # Fouten om te retryen
    open_timeout=30.0,    # Tijd in open state voor half-open
    success_threshold=3   # Aantal succesvolle operaties voor closed state
)
```

## States

1. **Closed**
   - Normale operatie
   - Retry bij tijdelijke fouten
   - Gaat open na max_retries

2. **Open**
   - Blokkeert alle operaties
   - Gaat half-open na open_timeout
   - Metrics voor rejected operaties

3. **Half-Open**
   - Test operaties toegestaan
   - Gaat open bij fouten
   - Gaat closed na success_threshold

## Metrics

### State Metrics
- `circuit_breaker_state`: Huidige state (0=closed, 1=open, 2=half-open)
- `circuit_breaker_errors_total`: Aantal fouten per type
- `circuit_breaker_recovery_time_seconds`: Hersteltijd histogram
- `circuit_breaker_operations_total`: Operatie counts met status

### Logging
- State changes met oude/nieuwe state
- Fouten met context
- Operatie resultaten

## Best Practices

1. **Configuratie**
   - Stel max_retries in op basis van SLA
   - Kies open_timeout op basis van hersteltijd
   - Specificeer relevante exceptions

2. **Monitoring**
   - Alert op hoge error rates
   - Track recovery times
   - Monitor state changes

3. **Error Handling**
   - Gebruik CircuitBreakerError voor fouten
   - Implementeer fallback logica
   - Log relevante context

## Voorbeeld Gebruik

```python
# MQTT Client met circuit breakers
client = MQTTClient(config)

# Publish met circuit breaker
await client.publish("topic", {"message": "test"})

# Subscribe met circuit breaker
await client.subscribe("topic", callback)
```

## Grafana Dashboards

Aanbevolen metrics voor monitoring:
1. Circuit breaker states over tijd
2. Error rates per breaker
3. Recovery times
4. Operation success rates 