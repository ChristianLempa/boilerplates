data "civo_size" "xsmall" {
    filter {
        key = "type"
        values = ["kubernetes"]
    }

    filter {
        key = "name"
        values = ["g4s.kube.xsmall"]
        match_by = "re"
    }
}

data "civo_size" "small" {
    filter {
        key = "type"
        values = ["kubernetes"]
    }

    filter {
        key = "name"
        values = ["g4s.kube.small"]
        match_by = "re"
    }
}

data "civo_size" "medium" {
    filter {
        key = "type"
        values = ["kubernetes"]
    }

    filter {
        key = "name"
        values = ["g4s.kube.medium"]
        match_by = "re"
    }
}
