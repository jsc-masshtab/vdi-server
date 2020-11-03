export interface IPendingAdd  {
    clusters: boolean;
    nodes: boolean;
    datapools: boolean;
    vms: boolean;
    templates: boolean;
    controllers: boolean;
}

export interface ISelectValue {
    value: {
        id?: string;
        verbose_name?: string;
        address?: string;
    }
}

export interface IFinishPoolView {
    verbose_name: string;
    connection_types: [string];
    type: string;
    cluster_name: string;
    node_name: string;
    datapool_name: string;
    vm_name: string; //stat
    template_name: string; // auto
    reserve_size: number;
    total_size: number;
    initial_size: number;
    vm_name_template: string; // auto
    create_thin_clones: boolean;//stat
    prepare_vms: boolean;
    increase_step: number;// autos
}

export interface IFinishPoolForm {
    connection_types: [string];
    verbose_name: string;
    cluster_id: string;
    node_id: string;
    datapool_id: string;
    vm_ids_list: string[]; //stat
    template_id: string; // auto
    vm_name_template: string;// auto
    controller_ip: string; //auto
    size: {
        total_size: number;
        initial_size: number;
        increase_step: number; //auto
        reserve_size: number;
    }
    create_thin_clones: boolean;//stat
    prepare_vms: boolean;
}
