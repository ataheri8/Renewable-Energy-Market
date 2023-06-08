-- alter nameplate_rating type from integer to float type as part of https://opusonesolutions.atlassian.net/browse/PM-1221
ALTER TABLE der_info ALTER COLUMN nameplate_rating TYPE NUMERIC(20,4);