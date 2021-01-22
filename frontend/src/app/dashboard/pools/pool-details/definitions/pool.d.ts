
export interface IPool extends ISettingsAutoPool, ISettingsStaticPool  {
  verbose_name: string;
  assigned_connection_types: [string];
  pool_type: string;
  vms: IPoolVms[];
  controller: {
    id: string;
    address: string;
  };
  users: {
    username: string;
  };

  resource_pool: {
    verbose_name: string;
  };

  template: {
    verbose_name: string;
  };

  create_thin_clones: boolean;
  prepare_vms: boolean;
  keep_vms_on: boolean;
}

export interface IPoolVms  {
  id: string;
  verbose_name: string;
  status: string;
  user: {
    username: string;
  },
  template: {
    verbose_name: string;
  }
}

export interface IPoolsVm {
  typePool: string;
  usersPool: [{username: string }];
  idPool: number;
}

interface ISettingsAutoPool {
  initial_size: number;
  increase_step: number;
  reserve_size: number;
  total_size: number;
  vm_name_template: string;
  ad_cn_pattern: string;
}

interface ISettingsStaticPool {
  resource_pool_id: string;
}

