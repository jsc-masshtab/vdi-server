
export interface IPool extends ISettingsAutoPool, ISettingsStaticPool  {
  verbose_name: string;
  pool_type: string;
  vms: IPoolVms;
  controller: {
    address: string;
  };
  users: {
    username: string;
  };

  cluster: {
    verbose_name: string;
  };

  node: {
    verbose_name: string;
  };

  datapool: {
    verbose_name: string;
  };

  template: {
    verbose_name: string;
  };

  create_thin_clones: boolean;
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

interface ISettingsAutoPool {
  initial_size: number;
  reserve_size: number;
  total_size: number;
  vm_name_template: string;
}

interface ISettingsStaticPool {
  cluster_id: string;
  node_id: string;
}
