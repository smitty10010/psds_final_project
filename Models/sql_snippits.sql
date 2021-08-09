--Seller and Buyers of Armed Drones and Loitering Munitions
SELECT buyer,
       seller,
       weapon,
       weapon_category,
       weapon_description,
       number_delivered,
       delivery_year,
       geom
FROM sipri
JOIN
    (SELECT borders.name,
            borders.geom
     FROM borders) borders ON borders.name = sipri.buyer
WHERE CASE
    WHEN LENGTH (delivery_year) > 4 THEN CAST(RIGHT(delivery_year,4) AS INTEGER)
    ELSE CAST(delivery_year AS INTEGER)
    END > 2000
AND weapon_description IN ('Loitering munition','Armed UAV')
ORDER BY seller,buyer;

-- Global Average of deaths Airstrike vs Drone Strike
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END sub_event_type,
       AVG(fatalities)::numeric(10,2) AS AVERAGE_DEATHS,
       stddev_samp(fatalities)::numeric(10,2) AS STD_DEATHS,
       SUM(fatalities) AS total_deaths,
       COUNT(*) AS total_drone_strikes
FROM acled
WHERE sub_event_type = 'Air/drone strike'
    AND notes LIKE '%drone%'
GROUP BY sub_event_type
UNION
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Air Strike'
       END sub_event_type,
       AVG(fatalities)::numeric(10,2) AS AVERAGE_DEATHS,
       stddev_samp(fatalities)::numeric(10,2) AS STD_DEATHS,
       SUM(fatalities) AS total_deaths,
       COUNT(*) AS total_air_strikes
FROM acled
WHERE sub_event_type = 'Air/drone strike'
    AND notes NOT ILIKE ALL (ARRAY['%drone%'])
GROUP BY sub_event_type
ORDER BY AVERAGE_DEATHS DESC

-- Libya Drone and Air Strikes
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    ( SELECT name,
             geom,
             cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country = 'Libya'
    AND year > 2011
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes LIKE '%drone%'
UNION
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Air Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    ( SELECT name,
             geom,
             cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country = 'Libya'
    AND year > 2011
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes NOT ILIKE ALL (ARRAY['%drone%'])
ORDER BY event_date

-- Libya Drone Strikes Near Turkish Drone Base
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop,
       CASE
           WHEN ST_DWithin(acled.geom,ST_GeogFromText('POINT(13.2833 32.9000)'),150000) THEN 1
           ELSE 0
       END Near_drone_base
FROM acled
CROSS JOIN LATERAL
    ( SELECT name,
             geom,
             cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country = 'Libya'
    AND year > 2011
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND (notes LIKE '%drone%'
         OR actor1 ILIKE ANY (ARRAY['Pro-GNA Faction and/or Military Forces of Turkey (2016-)',
                                    'Military Forces of Turkey (2016-)']))

-- Libya Drone vs Air Strikes and distance to city
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    ( SELECT name,
             geom,
             cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country = 'Libya'
    AND year > 2011
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND (notes LIKE '%drone%'
         OR actor1 ILIKE ANY (ARRAY['Military Forces of the United Arab Emirates (2004-)',
                                    'Pro-GNA Faction and/or Military Forces of Turkey (2016-)',
                                    'Pro-Haftar Faction and/or Military Forces of United Arab Emirates (2004-)',
                                    'Military Forces of Turkey (2016-)'])
         OR assoc_actor_1 ILIKE ANY (ARRAY['Military Forces of United Arab Emirates',
                                           'Military Forces of Egypt (2014-); Military Forces of United Arab Emirates',
                                           'Military Forces of the United Arab Emirates (2004-)']))
UNION
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Air Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    ( SELECT name,
             geom,
             cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country = 'Libya'
    AND year > 2011
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes NOT ILIKE ANY (ARRAY['%drone%'])
    AND ((actor1 != 'Military Forces of the United Arab Emirates (2004-)'
          AND actor1 != 'Pro-GNA Faction and/or Military Forces of Turkey (2016-)'
          AND actor1 != 'Pro-Haftar Faction and/or Military Forces of United Arab Emirates (2004-)'
          AND actor1 !='Military Forces of Turkey (2016-)')
         AND (assoc_actor_1 != 'Military Forces of United Arab Emirates'
              AND assoc_actor_1 != 'Military Forces of Egypt (2014-); Military Forces of United Arab Emirates'
              AND assoc_actor_1 != 'Military Forces of the United Arab Emirates (2004-)'
              OR assoc_actor_1 IS NULL))
-- Comparison of Armed Drones and Guided Missiles Sold
SELECT s2.buyer,
       s2.seller,
       s2.weapon,
       s2.weapon_description,
       s2.delivery_year
FROM
    (SELECT *
     FROM sipri
     WHERE CASE
               WHEN LENGTH (delivery_year) > 4 THEN CAST(RIGHT(delivery_year,4) AS INTEGER)
               ELSE CAST(delivery_year AS INTEGER)
           END > 2000
         AND weapon_description IN ('Armed UAV')) s
JOIN sipri s2 ON s.buyer = s2.buyer
WHERE s.buyer = s2.buyer
    AND s.seller = s2.seller
    AND s2.weapon_description IN ('ASM',
                                  'Guided bomb',
                                  'Anti-tank missile',
                                  'Armed UAV')
ORDER BY s2.seller,
         s2.buyer

-- Crosstab of air strikes by year
SELECT country,
       COALESCE("2000",0)"2000",
       COALESCE("2001",0) "2001",
       COALESCE("2002",0)"2002",
       COALESCE("2003",0)"2003",
       COALESCE("2004",0)"2004",
       COALESCE("2005",0)"2005",
       COALESCE("2006",0)"2006",
       COALESCE("2007",0)"2007",
       COALESCE("2008",0)"2008",
       COALESCE("2009",0)"2009",
       COALESCE("2010",0)"2010",
       COALESCE("2011",0)"2011",
       COALESCE("2012",0)"2012",
       COALESCE("2013",0)"2013",
       COALESCE("2014",0)"2014",
       COALESCE("2015",0)"2015",
       COALESCE("2016",0)"2016",
       COALESCE("2017",0)"2017",
       COALESCE("2018",0)"2018",
       COALESCE("2019",0)"2019",
       COALESCE("2020",0)"2020"
FROM crosstab($$
	SELECT country,year,COUNT(*) AS ct
	FROM acled
	WHERE sub_event_type = 'Air/drone strike'
	GROUP BY 1,2
	ORDER BY 1$$, $$ SELECT y FROM generate_series(2000,2020) y$$) AS ct(country text, "2000" bigint, "2001" bigint, "2002" bigint, "2003" bigint, "2004" bigint, "2005" bigint, "2006" bigint, "2007" bigint, "2008" bigint, "2009" bigint, "2010" bigint, "2011" bigint, "2012" bigint, "2013" bigint, "2014" bigint, "2015" bigint, "2016" bigint, "2017" bigint, "2018" bigint, "2019" bigint, "2020" bigint);

-- Count of Countries with Drone Strikes
SELECT country,CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END sub_event_type,
       COUNT(*) AS total_drone_strikes
FROM acled
WHERE sub_event_type = 'Air/drone strike'
    AND notes LIKE '%drone%'
GROUP BY country,sub_event_type
ORDER BY total_drone_strikes DESC

--center geos for buyer and seller of drones
SELECT s2.buyer,
       s2.seller,
       s2.weapon,
       s2.weapon_description,
       coalesce(s2.number_delivered,0),
       s2.delivery_year,
       ST_Y(ST_centroid(s.seller_location)) AS seller_center_lat,
       ST_X(ST_Centroid(s.seller_location)) AS seller_center_lon,
       ST_Y(ST_centroid(s.buyer_location)) AS buyer_center_lat,
       ST_X(ST_Centroid(s.buyer_location)) AS buyer_center_lon
FROM
    (SELECT *,
            geo1.geom AS seller_location,
            geo2.geom AS buyer_location
     FROM sipri
     JOIN borders geo1 ON sipri.seller = geo1.admin
     JOIN borders geo2 ON sipri.buyer = geo2.admin
     WHERE CASE
               WHEN LENGTH(delivery_year) > 4 THEN CAST(RIGHT(delivery_year, 4) AS INTEGER)
               ELSE CAST(delivery_year AS INTEGER)
           END > 2000
         AND weapon_description IN('Armed UAV')) s
JOIN sipri s2 ON s.buyer = s2.buyer
WHERE s.buyer = s2.buyer
    AND s.seller = s2.seller
    AND s2.weapon_description IN('ASM',
                                 'Guided bomb',
                                 'Anti-tank missile',
                                 'Armed UAV')
ORDER BY s2.seller,
         s2.buyer;

-- Select all drone and airstrke data between 2000 and 2021 
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Drone Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    (SELECT name,
            geom,
            cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country IN ('Afghanistan',
                  'Syria',
                  'Iraq',
                  'Yemen',
                  'Pakistan',
                  'Mali',
                  'Turkey',
                  'Ukraine',
                  'Azerbaijan',
                  'Saudi Arabia',
                  'Palestine',
                  'Armenia',
                  'Libya',
                  'Burkina Faso',
                  'Somalia',
                  'Egypt',
                  'Israel',
                  'Lebanon',
                  'Venezuela',
                  'United Arab Emirates',
                  'Nigeria',
                  'South Sudan')
    AND year > 2000
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes LIKE '%drone%'
UNION
SELECT CASE
           WHEN sub_event_type = 'Air/drone strike' THEN 'Air Strike'
       END type_of_strike,
       acled.*,
       ST_Distance(acled.geom::geography,cities.geom::geography) AS distance_to_nearest_city,
       cities.name AS nearest_city,
       cities.gn_pop
FROM acled
CROSS JOIN LATERAL
    (SELECT name,
            geom,
            cities.gn_pop
     FROM cities
     WHERE gn_pop > 0
     ORDER BY cities.geom <-> acled.geom
     LIMIT 1) cities
WHERE country IN ('Afghanistan',
                  'Syria',
                  'Iraq',
                  'Yemen',
                  'Pakistan',
                  'Mali',
                  'Turkey',
                  'Ukraine',
                  'Azerbaijan',
                  'Saudi Arabia',
                  'Palestine',
                  'Armenia',
                  'Libya',
                  'Burkina Faso',
                  'Somalia',
                  'Egypt',
                  'Israel',
                  'Lebanon',
                  'Venezuela',
                  'United Arab Emirates',
                  'Nigeria',
                  'South Sudan')
    AND year > 2000
    AND year < 2021
    AND sub_event_type = 'Air/drone strike'
    AND notes NOT ILIKE ALL (ARRAY['%drone%'])
ORDER BY event_date;