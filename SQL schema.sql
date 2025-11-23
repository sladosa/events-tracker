-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.areas (
  id uuid NOT NULL,
  user_id uuid,
  template_id uuid,
  name text NOT NULL,
  icon text,
  color text,
  sort_order integer NOT NULL,
  description text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  slug text NOT NULL,
  CONSTRAINT areas_pkey PRIMARY KEY (id),
  CONSTRAINT areas_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT areas_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.templates(id)
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
  CONSTRAINT events_pkey PRIMARY KEY (id),
  CONSTRAINT events_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT events_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id)
);
CREATE TABLE public.name_change_history (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  object_type text NOT NULL CHECK (object_type = ANY (ARRAY['area'::text, 'category'::text, 'attribute'::text])),
  object_id uuid NOT NULL,
  old_name text,
  new_name text,
  changed_by uuid,
  changed_at timestamp with time zone DEFAULT now(),
  change_reason text,
  CONSTRAINT name_change_history_pkey PRIMARY KEY (id),
  CONSTRAINT name_change_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES auth.users(id)
);
CREATE TABLE public.template_versions (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  version_number integer NOT NULL,
  snapshot_data jsonb NOT NULL,
  created_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  description text,
  CONSTRAINT template_versions_pkey PRIMARY KEY (id),
  CONSTRAINT template_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id)
);
CREATE TABLE public.templates (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  description text,
  icon text,
  is_public boolean DEFAULT false,
  created_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  user_id uuid,
  CONSTRAINT templates_pkey PRIMARY KEY (id),
  CONSTRAINT templates_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id),
  CONSTRAINT templates_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);