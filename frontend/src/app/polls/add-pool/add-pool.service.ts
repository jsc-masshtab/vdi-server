import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class AddPoolService {

    constructor(private service: Apollo) { }

    public getAllClusters(ip?: string): QueryRef<any, any> {
        const ipController = ip;
        if (ipController) {
            return this.service.watchQuery({
                query: gql` query allClusters($ip: String) {
                                controller(ip: $ip) {
                                    clusters {
                                        id
                                        verbose_name
                                    }
                                }
                            }
                        `,
                variables: {
                    method: 'GET',
                    ip: ipController
                }
            });
        } else {
            return this.service.watchQuery({
                query: gql` query allClusters {
                            controllers {
                                clusters {
                                    id
                                    verbose_name
                                }
                            }
                        }
                        `,
                variables: {
                    method: 'GET'
                }
            });
        }
    }

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

    public getAllTemplates(ip: string): QueryRef<any, any> {
        const ipController = ip;
        return  this.service.watchQuery({
            query:  gql` query allTemplates($ip: String) {
                                controller(ip: $ip) {
                                    templates {
                                        info
                                    }
                                }
                            }
                        `,
            variables: {
                method: 'GET',
                ip: ipController
            }
        });
    }

    public getAllControllers(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query allControllers {
                            controllers {
                                ip
                                description
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public createDinamicPool(name: string, templateId: string, clusterId: string,
                             nodeId: string, datapoolId: string, initialSize: number,
                             reserveSize: number, totalSize: number) {

        const idTemplate = templateId;
        const namePool = name;
        const idCluster = clusterId;
        const idNode = nodeId;
        const idDatapool = datapoolId;
        const initialSizePool = initialSize;
        const reserveSizePool = reserveSize;
        const totalSizePool = totalSize;
        return this.service.mutate<any>({
            mutation: gql`
                        mutation AddPool($name: String!,$template_id: String,
                                        $cluster_id: String,$node_id: String,
                                        $datapool_id: String,$initial_size: Int,
                                        $reserve_size: Int,$total_size: Int)
                                {
                                addPool(name: $namePool, template_id: $idTemplate,
                                        cluster_id: $idCluster,node_id: $idNode,
                                        datapool_id: $idDatapool,initial_size: $initialSizePool,
                                        reserve_size: $reserveSizePool,total_size:$totalSizePool)
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
                total_size: totalSizePool
            }
        });
    }

    public createStaticPool(name: string, clusterId: string, nodeId: string, datapoolId: string, vmsIdsList: string[]) {
        const namePool = name;
        const idCluster = clusterId;
        const idNode = nodeId;
        const idDatapool = datapoolId;
        const idsVms = vmsIdsList;
        return this.service.mutate<any>({
            mutation: gql`
                        mutation AddPool($name: String!,$cluster_id: String,$node_id: String,
                                        $datapool_id: String,$vm_ids_list: [String]) {
                            addStaticPool(name: $name,cluster_id: $idCluster,
                                          node_id: idNode,datapool_id: $idDatapool,
                                          vm_ids_list: $vmsIdsList)
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
