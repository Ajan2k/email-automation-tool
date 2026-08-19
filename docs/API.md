# API Reference (summary)

Interactive docs: `GET /docs` (Swagger UI) once the backend is running.

## Auth
| Method | Path | Description |
|---|---|---|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | OAuth2 form login → JWT |
| GET | /api/auth/me | Current user |

## Contacts & Companies
| POST/GET | /api/contacts | Create / list (server-side pagination, search, filters) |
| GET/PATCH/DELETE | /api/contacts/{id} | Read / update / delete |
| POST/GET | /api/companies | Create / list |

## Imports
| POST | /api/imports/preview | Upload .xlsx/.csv → validation summary (valid/invalid/duplicates) |
| POST | /api/imports/run | Execute the import (bulk insert) |
| GET | /api/imports | Import history |

## Templates
| POST/GET | /api/templates | Create / list |
| PATCH/DELETE | /api/templates/{id} | Update / delete |
| POST | /api/templates/{id}/preview | Render with sample or real contact |

## Campaigns
| POST/GET | /api/campaigns | Create / list |
| GET | /api/campaigns/{id}/stats | Per-campaign funnel stats |
| POST | /api/campaigns/{id}/launch\|pause\|cancel | State transitions |

## Tracking (public)
| GET | /api/track/open/{tracking_id} | 1×1 pixel, records open |
| GET | /api/track/click/{tracking_id}?url= | Records click, redirects |
| GET | /api/track/unsubscribe/{tracking_id} | Unsubscribes + suppresses |

## Webhooks
| POST | /api/webhooks/inbound-email | Reply ingestion → conversation → AI draft |
| POST | /api/webhooks/bounce | Bounce → suppression list |

## Conversations & AI replies
| GET | /api/conversations | Inbox (filter by status/classification) |
| GET | /api/conversations/{id} | Full thread |
| GET | /api/ai-replies?status=draft | Pending reviews |
| PATCH | /api/ai-replies/{id} | Edit draft body |
| POST | /api/ai-replies/{id}/regenerate\|reject\|approve | Review actions |

## Analytics
| GET | /api/analytics/dashboard | Sent/delivered/opened/clicked/replied/bounced + rates |
