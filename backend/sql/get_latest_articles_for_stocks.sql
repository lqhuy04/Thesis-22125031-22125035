-- Run this script once in the Supabase SQL Editor.
-- It returns at most N latest stock articles for each requested stock ID.

create index if not exists idx_article_stock_stock_id_text
    on public."Article_Stock" ((stock_id::text));

create or replace function public.get_latest_articles_for_stocks(
    p_stock_ids text[],
    p_articles_per_stock integer default 2
)
returns table (
    stock_id text,
    id text,
    title text,
    sentiment text
)
language sql
stable
security invoker
set search_path = public
as $$
    with ranked_articles as (
        select
            article_stock.stock_id::text as stock_id,
            article.id::text as id,
            coalesce(article.title::text, '') as title,
            article.sentiment::text as sentiment,
            row_number() over (
                partition by article_stock.stock_id
                order by article.time desc nulls last, article.id desc
            ) as row_number
        from public."Article_Stock" as article_stock
        join public."Article" as article
          on article.id = article_stock.article_id
        where article_stock.stock_id::text = any(
            coalesce(p_stock_ids, array[]::text[])
        )
          and article.article_type = 'stock'
          and article.time is not null
    )
    select
        ranked_articles.stock_id,
        ranked_articles.id,
        ranked_articles.title,
        ranked_articles.sentiment
    from ranked_articles
    where ranked_articles.row_number <= greatest(
        coalesce(p_articles_per_stock, 2),
        1
    )
    order by
        array_position(p_stock_ids, ranked_articles.stock_id),
        ranked_articles.row_number;
$$;

comment on function public.get_latest_articles_for_stocks(text[], integer) is
    'Returns the latest N stock-type articles for each requested stock ID.';

grant execute on function public.get_latest_articles_for_stocks(text[], integer)
    to anon, authenticated, service_role;
