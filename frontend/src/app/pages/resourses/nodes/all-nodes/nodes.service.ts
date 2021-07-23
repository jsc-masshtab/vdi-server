import { IParams } from '../../../../../../types';
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class NodesService {

    constructor(private service: Apollo) {}

    public paramsForGetNodes: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllNodes(filter?): QueryRef<any, any> {

        let query: string = `query resources($ordering:String) {
            nodes(ordering: $ordering) {
                id
                verbose_name
                status
                datacenter_name
                cpu_count
                memory_count
                management_ip
                controller {
                    id
                    verbose_name
                }
            }
        }`

        if (filter) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $resource_pool_id: UUID, $ordering:String) {
                controller(id_:$controller_id) {
                    id
                    nodes(cluster_id: $cluster_id, resource_pool_id: $resource_pool_id, ordering: $ordering) {
                        id
                        verbose_name
                        status
                        cpu_count
                        memory_count
                        management_ip
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.paramsForGetNodes.nameSort,
                ...filter
            }
        });
    }

    public getNode(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            node(node_id: $id, controller_id: $controller_address) {
                                verbose_name
                                description
                                status
                                cpu_count
                                memory_count
                                management_ip
                                cluster_name
                                datacenter_name
                                node_plus_controller_installation
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

