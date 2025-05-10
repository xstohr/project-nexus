module.exports = {
  accounts: {
    input: {
      target: './src/lib/api/specs/accounts.yaml',
    },
    output: {
      mode: 'tags-split',
      target: './src/lib/api/generated/accounts',
      schemas: './src/lib/api/generated/accounts/model',
      client: 'react-query',
      mock: false,
      tsconfig: './orval.tsconfig.json',
      override: {
        mutator: {
          path: './src/lib/api/mutator/custom-instance.ts',
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
          useInfiniteQueryParam: 'nextPageToken',
          useQueryOptions: true,
        },
      },
    },
  },
  workspaces: {
    input: {
      target: './src/lib/api/specs/workspaces.yaml',
    },
    output: {
      mode: 'tags-split',
      target: './src/lib/api/generated/workspaces',
      schemas: './src/lib/api/generated/workspaces/model',
      client: 'react-query',
      mock: false,
      tsconfig: './orval.tsconfig.json',
      override: {
        mutator: {
          path: './src/lib/api/mutator/custom-instance.ts',
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
          useInfiniteQueryParam: 'nextPageToken',
          useQueryOptions: true,
        },
      },
    },
  },
  tasks: {
    input: {
      target: './src/lib/api/specs/tasks.yaml',
    },
    output: {
      mode: 'tags-split',
      target: './src/lib/api/generated/tasks',
      schemas: './src/lib/api/generated/tasks/model',
      client: 'react-query',
      mock: false,
      tsconfig: './orval.tsconfig.json',
      override: {
        mutator: {
          path: './src/lib/api/mutator/custom-instance.ts',
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
          useInfiniteQueryParam: 'nextPageToken',
          useQueryOptions: true,
        },
      },
    },
  },
  comments: {
    input: {
      target: './src/lib/api/specs/comments.yaml',
    },
    output: {
      mode: 'tags-split',
      target: './src/lib/api/generated/comments',
      schemas: './src/lib/api/generated/comments/model',
      client: 'react-query',
      mock: false,
      tsconfig: './orval.tsconfig.json',
      override: {
        mutator: {
          path: './src/lib/api/mutator/custom-instance.ts',
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
          useInfiniteQueryParam: 'nextPageToken',
          useQueryOptions: true,
        },
      },
    },
  },
  main: {
    input: {
      target: './src/lib/api/specs/main.yaml',
    },
    output: {
      mode: 'tags-split',
      target: './src/lib/api/generated/main',
      schemas: './src/lib/api/generated/main/model',
      client: 'react-query',
      mock: false,
      tsconfig: './orval.tsconfig.json',
      override: {
        mutator: {
          path: './src/lib/api/mutator/custom-instance.ts',
          name: 'customInstance',
        },
        query: {
          useQuery: true,
          useInfinite: true,
          useInfiniteQueryParam: 'nextPageToken',
          useQueryOptions: true,
        },
      },
    },
  },
}; 