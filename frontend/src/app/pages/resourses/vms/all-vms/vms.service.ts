import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';

@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllVms(filter?, refresh?): QueryRef<any, any> {

        let query: string = `query resources($ordering:ShortString) {
            vms(ordering: $ordering) {
                verbose_name
                pool_name
                status
                user_power_state
                id
                controller {
                    id
                    verbose_name
                }
            }
        }`

        if (filter) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $resource_pool_id: UUID, $node_id: UUID, $ordering:ShortString) {
                controller(id_:$controller_id) {
                    id
                    vms(cluster_id: $cluster_id, resource_pool_id: $resource_pool_id, node_id: $node_id, exclude_existed: false, ordering: $ordering) {
                        id
                        verbose_name
                        status
                        pool_name
                        user_power_state
                    }
                }
            }`
        } else if (refresh && !filter) {
            query = `query resources($ordering:ShortString, $refresh: Boolean) {
                vms(ordering: $ordering, refresh: $refresh) {
                    verbose_name
                    pool_name
                    status
                    user_power_state
                    id
                    controller {
                        id
                        verbose_name
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.params.nameSort,
                ...filter,
                refresh
            }
        });
    }

    public getVm(id: string, controller_address: string, refresh: boolean): QueryRef<any, any> {

        let query: string = ` query resources($id: UUID, $controller_address: UUID) {
                                vm(vm_id: $id, controller_id: $controller_address) {
                                    verbose_name
                                    description
                                    os_type
                                    os_version
                                    cpu_count
                                    memory_count
                                    tablet
                                    ha_enabled
                                    disastery_enabled
                                    guest_agent
                                    remote_access
                                    spice_stream
                                    user_power_state
                                    boot_type
                                    start_on_boot
                                    address
                                    status
                                    hostname
                                    domain_tags {
                                        colour
                                        verbose_name
                                    }
                                    parent_name
                                    resource_pool {
                                        id
                                        verbose_name
                                    }
                                }
                            }`

        if (refresh) {
          query = ` query resources($id: UUID, $controller_address: UUID, $refresh: Boolean) {
                      vm(vm_id: $id, controller_id: $controller_address, refresh: $refresh) {
                          verbose_name
                          description
                          os_type
                          os_version
                          cpu_count
                          memory_count
                          tablet
                          ha_enabled
                          disastery_enabled
                          guest_agent
                          remote_access
                          spice_stream
                          user_power_state
                          boot_type
                          start_on_boot
                          address
                          status
                          hostname
                          domain_tags {
                              colour
                              verbose_name
                          }
                          parent_name
                          resource_pool {
                              id
                              verbose_name
                          }
                      }
                  }`
        }
        return this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                id,
                controller_address,
                refresh
            }
        });
    }

    public attachVeilUtils(data) {
        return this.service.mutate<any>({
            mutation: gql` mutation resources($id: UUID!, $controller_id: UUID!) {
                            attachVeilUtils(domain_id: $id, controller_id: $controller_id) {
                                ok
                            }
                        }
                    `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }
}
