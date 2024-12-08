local cmp = require('cmp')

cmp.setup({
  snippet = {
    expand = function(args)
      vim.fn["UltiSnips#Anon"](args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ['<S-Tab>'] = cmp.mapping.select_prev_item(),
    ['<Tab>'] = cmp.mapping.select_next_item(),
  }),
  sources = cmp.config.sources(
    {
      { name = 'nvim_lsp_signature_help' },
      { name = 'nvim_lsp' },
    },
    {
      { name = 'buffer' },
    }
  )
})

cmp.setup.filetype('gitcommit', {
  sources = cmp.config.sources(
    {
      { name = 'cmp_git' },
    },
    {
      { name = 'buffer' },
    }
  )
})

cmp.setup.cmdline('/', {
  mapping = cmp.mapping.preset.cmdline(),
  sources = {
    { name = 'buffer' }
  }
})

cmp.setup.cmdline(':', {
  mapping = cmp.mapping.preset.cmdline(),
  sources = cmp.config.sources(
    {
      { name = 'path' }
    },
    {
      { name = 'cmdline' }
    }
  )
})
