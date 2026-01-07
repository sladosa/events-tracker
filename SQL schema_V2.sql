-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.activity_presets (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  name text NOT NULL,
  area_id uuid,
  category_id uuid,
  usage_count integer DEFAULT 0,
  last_used timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT activity_presets_pkey PRIMARY KEY (id),
  CONSTRAINT activity_presets_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT activity_presets_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(id),
  CONSTRAINT activity_presets_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id)
);
CREATE TABLE public.areas (
  id uuid NOT NULL,
  user_id uuid,
  name text NOT NULL,
  icon text,
  color text,
  sort_order integer NOT NULL,
  description text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  slug text NOT NULL,
  CONSTRAINT areas_pkey PRIMARY KEY (id),
  CONSTRAINT areas_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.attribute_definitions (
  id uuid NOT NULL,
  category_id uuid,
  name text NOT NULL,
  data_type text NOT NULL CHECK (data_type = ANY (ARRAY['number'::text, 'text'::text, 'datetime'::text, 'boolean'::text, 'link'::text, 'image'::text])),
  unit text,
  is_required boolean DEFAULT false,
  default_value text,
  validation_rules jsonb DEFAULT '{}'::jsonb,
  sort_order integer NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  user_id uuid,
  slug text NOT NULL,
  description text,
  CONSTRAINT attribute_definitions_pkey PRIMARY KEY (id),
  CONSTRAINT attribute_definitions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id),
  CONSTRAINT attribute_definitions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.categories (
  id uuid NOT NULL,
  area_id uuid,
  parent_category_id uuid,
  name text NOT NULL,
  description text,
  level integer NOT NULL CHECK (level >= 1 AND level <= 10),
  sort_order integer NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  user_id uuid,
  slug text NOT NULL,
  path USER-DEFINED,
  CONSTRAINT categories_pkey PRIMARY KEY (id),
  CONSTRAINT categories_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(id),
  CONSTRAINT categories_parent_category_id_fkey FOREIGN KEY (parent_category_id) REFERENCES public.categories(id),
  CONSTRAINT categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.data_shares (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  owner_id uuid NOT NULL,
  grantee_id uuid NOT NULL,
  share_type text NOT NULL CHECK (share_type = ANY (ARRAY['area'::text, 'category'::text])),
  target_id uuid NOT NULL,
  permission text NOT NULL CHECK (permission = ANY (ARRAY['read'::text, 'write'::text])),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  note text,
  CONSTRAINT data_shares_pkey PRIMARY KEY (id),
  CONSTRAINT data_shares_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id),
  CONSTRAINT data_shares_grantee_id_fkey FOREIGN KEY (grantee_id) REFERENCES auth.users(id)
);
CREATE TABLE public.event_attachments (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  event_id uuid,
  type text CHECK (type = ANY (ARRAY['image'::text, 'link'::text, 'file'::text])),
  url text NOT NULL,
  filename text,
  size_bytes integer,
  created_at timestamp with time zone DEFAULT now(),
  user_id uuid,
  CONSTRAINT event_attachments_pkey PRIMARY KEY (id),
  CONSTRAINT event_attachments_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id),
  CONSTRAINT event_attachments_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.event_attributes (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  event_id uuid,
  attribute_definition_id uuid,
  value_text text,
  value_number numeric,
  value_datetime timestamp with time zone,
  value_boolean boolean,
  value_json jsonb,
  created_at timestamp with time zone DEFAULT now(),
  user_id uuid,
  CONSTRAINT event_attributes_pkey PRIMARY KEY (id),
  CONSTRAINT event_attributes_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.events(id),
  CONSTRAINT event_attributes_attribute_definition_id_fkey FOREIGN KEY (attribute_definition_id) REFERENCES public.attribute_definitions(id),
  CONSTRAINT event_attributes_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);
CREATE TABLE public.events (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid,
  category_id uuid,
  event_date date NOT NULL,
  comment text,
  created_at timestamp with time zone DEFAULT now(),
  edited_at timestamp with time zone DEFAULT now(),
  session_start timestamp with time zone,
  CONSTRAINT events_pkey PRIMARY KEY (id),
  CONSTRAINT events_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT events_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id)
);