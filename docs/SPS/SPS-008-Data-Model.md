# SPS-008 — Data Model

**Status:** Approved  
**Version:** 1.0

## Core Entities

- Creator
- Stream Session
- Connector
- Event
- Analytics
- Insight
- Recommendation
- Goal
- Report
- Diagnostic

## Pipeline

Events produce Analytics.  
Analytics generate Insights.  
Insights support Recommendations.  
Reports present Analytics, Insights, and Recommendations.

## Ownership

Creators own their generated data.

## Non-Goal

This is not a database schema.
