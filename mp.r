#require(jsonlite)

mp <- function(results.path, key.path) {
    results <- read.csv(results.path)
    #results.va <- fromJSON(results$var_arrays)
    key <- read.delim(key.path)

    ids <- (1:dim(results)[1])
    d <- data.frame(ans.human=results[,1],
                    ans.model=key$intruder.idx[ids],
                    experiment=factor(key$experiment[ids]))
    d$correct <- d$ans.human == d$ans.model
    d$total <- rep(1, dim(d)[1])

    d.agg <- aggregate(cbind(correct, total) ~ experiment,
                       data=d,
                       FUN=sum)
    d.agg$mp <- d.agg$correct / d.agg$total

    d.agg
}

results.path <- 'wiki-ru-dll.big.results.nocr.csv'
key.path <- 'wiki-ru-dll-lda-trunc50-big.key.tsv'
head(mp(results.path, key.path))
