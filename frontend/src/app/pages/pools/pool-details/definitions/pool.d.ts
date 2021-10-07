
export interface IPool extends ISettingsAutoPool, ISettingsStaticPool  {
  verbose_name: string;
  assigned_connection_types: [string];
  pool_type: string;
  vms: IPoolVms[];
  controller: {
    id: string;
    address: string;
    verbose_name: string;
  };
  users: {
    id: string;
    username: string;
  };

  resource_pool: {
    verbose_name: string;
  };

  template: {
    verbose_name: string;
  };

  create_thin_clones: boolean;
  enable_vms_remote_access: boolean;
  start_vms: boolean;
  set_vms_hostnames: boolean;
  include_vms_in_ad: boolean;
  keep_vms_on: boolean;
  status: string;
}

export interface IPoolVms  {
  id: string;
  verbose_name: string;
  status: string;
  user: {
    id: string;
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
  ad_ou: string;
}

interface ISettingsStaticPool {
  resource_pool_id: string;
}

