import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { IParams } from 'types';

@Injectable()
export class VmsService {

    constructor(private service: Apollo) {}

    public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllVms(filter?): QueryRef<any, any> {

        let query: string = `query resources($ordering:String) {
            vms(ordering: $ordering) {
                verbose_name
                status
                id
                controller {
                    id
                    verbose_name
                }
            }
        }`

        if (filter) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $node_id: UUID, $data_pool_id: UUID) {
                controller(id_:$controller_id) {
                    id
                    vms(cluster_id: $cluster_id, node_id: $node_id, data_pool_id: $data_pool_id, exclude_existed: false) {
                        id
                        verbose_name
                        status
                        template{
                            id
                            verbose_name
                        }
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.params.nameSort,
                ...filter
            }
        });
    }

    public getVm(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
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
                                vmachine_infs_count
                                vdisks_count
                                luns_count
                                vfunctions_count
                                user_power_state
                                boot_type
                                start_on_boot
                                node {
                                    id
                                    verbose_name
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}
