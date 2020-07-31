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

    public getAllNodes(): QueryRef<any, any> {

        return  this.service.watchQuery({
            query:  gql` query resources($ordering:String) {
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
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetNodes.nameSort
            }
        });
    }

    public getNode(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            node(node_id: $id, controller_id: $controller_address) {
                                verbose_name
                                status
                                cpu_count
                                memory_count
                                management_ip
                                cluster_name
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

