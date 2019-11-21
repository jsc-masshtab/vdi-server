import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class AddPoolService {

    constructor(private service: Apollo) { }

    // public getAllClusters(controller_ip?: string): QueryRef<any, any> {
    //     if (controller_ip) {
    //         return this.service.watchQuery({
    //             query: gql` query resources($controller_ip: String) {
    //                                 clusters(controller_ip: $controller_ip) {
    //                                     id
    //                                     verbose_name
    //                                 }
    //                             }
    //                         }
    //                     `,
    //             variables: {
    //                 method: 'GET',
    //                 controller_ip
    //             }
    //         });
    //     } else {
    //         return this.service.watchQuery({
    //             query: gql` query resources {
    //                             clusters {
    //                                 id
    //                                 verbose_name
    //                             }
    //                         }
    //                     `,
    //             variables: {
    //                 method: 'GET'
    //             }
    //         });
    //     }
    // }

    public getAllNodes(clusterId?: string): QueryRef<any, any> {
        const idCluster = clusterId;
        return  this.service.watchQuery({
            query:  gql` query allNodes($cluster_id: String) {
                            controllers {
                                nodes(cluster_id: $cluster_id) {
                                    id
                                    verbose_name
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                cluster_id: idCluster
            }
        });
    }

    public getAllDatapools(nodeId: string): QueryRef<any, any> {
        const idNode = nodeId;
        return  this.service.watchQuery({
            query:  gql` query allDatapools($node_id: String) {
                            controllers {
                                datapools(node_id: $node_id) {
                                    id
                                    verbose_name
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                node_id: idNode
            }
        });
    }

    public getAllVms(clusterId: string, nodeId: string, datapoolId: string): QueryRef<any, any> {
        const idCluster = clusterId;
        const idNode = nodeId;
        const idDatapool =  datapoolId;
        return  this.service.watchQuery({
            query:  gql` query list_free_vms($cluster_id: String,$node_id:String,$datapool_id:String) {
                                    list_of_vms(cluster_id: $cluster_id,node_id:$node_id,datapool_id:$datapool_id) {
                                        id
                                        name
                                    }
                                }
                    `,
            variables: {
                method: 'GET',
                cluster_id: idCluster,
                node_id: idNode,
                datapool_id: idDatapool,
                get_vms_in_pools: false
            }
        });
    }

    public getAllTemplates(controller_ip: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql`query vms($controller_ip: String) {
                            templates(controller_ip: $controller_ip) {
                                id
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                controller_ip
            }
        });
    }

    // l` query vms($controller_ip: String) {
    //     templates(controller_ip: $controller_ip) {
    //         id
    //         verbose_name
    //     }
    // }

    public getAllControllers(): QueryRef<any, any> { // +
        return  this.service.watchQuery({
            query:  gql` query controllers {
                            controllers {
                                address
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public createDinamicPool(namePool: string, idTemplate: string, idCluster: string,
                             idNode: string, idDatapool: string, initialSizePool: number,
                             reserveSizePool: number, totalSizePool: number, templateForVM: string, controllerIp: string) {

        return this.service.mutate<any>({
            mutation: gql`
                        mutation AddPool($name: String!,$template_id: String,
                                        $cluster_id: String,$node_id: String,
                                        $datapool_id: String,$initial_size: Int,
                                        $reserve_size: Int,$total_size: Int,
                                        $vm_name_template: String,
                                        $controller_ip: String!)
                                {
                                addPool(name: $name, template_id: $template_id,
                                        cluster_id: $cluster_id,node_id: $node_id,
                                        datapool_id: $datapool_id,initial_size: $initial_size,
                                        reserve_size: $reserve_size,total_size:$total_size,
                                        vm_name_template: $vm_name_template,
                                        controller_ip: $controller_ip
                                        )
                                        {
                                            id
                                        }
                            }
            `,
            variables: {
                method: 'POST',
                name: namePool,
                template_id: idTemplate,
                cluster_id: idCluster,
                node_id: idNode,
                datapool_id: idDatapool,
                initial_size: initialSizePool,
                reserve_size: reserveSizePool,
                total_size: totalSizePool,
                vm_name_template: templateForVM,
                controller_ip: controllerIp
            }
        });
    }

    public createStaticPool(namePool: string, idCluster: string, idNode: string, idDatapool: string, idsVms: string[]) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation AddPool($name: String!,$cluster_id: String,$node_id: String,
                                        $datapool_id: String,$vm_ids_list: [String]) {
                            addStaticPool(name: $name,cluster_id: $cluster_id,
                                          node_id: $node_id,datapool_id: $datapool_id,
                                          vm_ids_list: $vm_ids_list)
                                        {
                                            id
                                        }
                        }
            `,
            variables: {
                method: 'POST',
                name: namePool,
                cluster_id: idCluster,
                node_id: idNode,
                datapool_id: idDatapool,
                vm_ids_list: idsVms
            }
        });
    }
}
