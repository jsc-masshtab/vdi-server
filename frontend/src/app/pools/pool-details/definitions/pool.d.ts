
export interface IPool {
  name: string;
  desktop_pool_type: string;
  vms: IPoolVms;
  controller: {
    ip: string;
  };
  users: {
    username: string;
  };
  pool_resources_names: {
    cluster_name: string;
    node_name: string;
    datapool_name: string;
    template_name?: string; //auto
  };
  settings: Partial<ISettingsAutoPool> & Partial<ISettingsStaticPool>;
}

interface IPoolVms  {
  id: string;
  name: string;
  state: string;
  user: {
    username: string;
  },
  template?: { //auto
    name: string;
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

