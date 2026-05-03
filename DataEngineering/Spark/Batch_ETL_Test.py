# -*- coding: utf-8 -*-
"""
Created on Sat Jan 31 13:32:05 2026

@author: Nils
"""

import pyspark
from pyspark.sql import SparkSession
import unittest

load_schema = pyspark.sql.types.StructType([
    pyspark.sql.types.StructField("Country", pyspark.sql.types.StringType(), nullable = True),
    pyspark.sql.types.StructField("Date", pyspark.sql.types.StringType(), nullable = True),
    pyspark.sql.types.StructField("Cases", pyspark.sql.types.IntegerType(), nullable = True),
    pyspark.sql.types.StructField("Deaths", pyspark.sql.types.IntegerType(), nullable = True),
    pyspark.sql.types.StructField("Recoveries", pyspark.sql.types.IntegerType(), nullable = True)
])

transform_schema = pyspark.sql.types.StructType([
    pyspark.sql.types.StructField("Country", pyspark.sql.types.StringType(), nullable = True),
    pyspark.sql.types.StructField("Date", pyspark.sql.types.DateType(), nullable = True),
    pyspark.sql.types.StructField("Cases", pyspark.sql.types.IntegerType(), nullable = True),
    pyspark.sql.types.StructField("Deaths", pyspark.sql.types.IntegerType(), nullable = True),
    pyspark.sql.types.StructField("Recoveries", pyspark.sql.types.IntegerType(), nullable = True),
    pyspark.sql.types.StructField("SANITY_CHECK", pyspark.sql.types.BooleanType(), nullable = True),
    pyspark.sql.types.StructField("Mortality_Rate", pyspark.sql.types.DoubleType(), nullable = True),
    pyspark.sql.types.StructField("Recovery_Rate", pyspark.sql.types.DoubleType(), nullable = True),
    pyspark.sql.types.StructField("Mortality_Rate_Change", pyspark.sql.types.DoubleType(), nullable = True),
    pyspark.sql.types.StructField("Recovery_Rate_Change", pyspark.sql.types.DoubleType(), nullable = True)
])

class PySparkTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark = SparkSession.builder.appName("Batch_ETL_Pipelien_Test").getOrCreate()
        cls.logger = Batch_ETL_Functions.initialize_logger(mode = "a")


    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        
from pyspark.testing.utils import assertDataFrameEqual
import Batch_ETL_Functions

class TestETL(PySparkTestCase):
    def test_load(self):
        self.logger.info("\nStart testing data loading")
        sample_df = Batch_ETL_Functions.extract_all_data(self.spark, self.logger, test = True)
        expected_df = self.spark.read.csv("BatchData/Test/Covid/Load_Data_End", schema = load_schema, header = True)
        assertDataFrameEqual(sample_df, expected_df, rtol = 1e-1)
    
    def test_transform(self):
        self.logger.info("\nStart Testing Transformations")
        sample_data = self.spark.read.csv("BatchData/Test/Covid/Load_Data_End", header = True, schema = load_schema)
        
        computed_df = Batch_ETL_Functions.Transform(sample_data, self.logger)
        
        expected_df = self.spark.read.csv("BatchData/Test/Covid/Transform_Test", header = True, schema = transform_schema)
        assertDataFrameEqual(computed_df, expected_df, rtol=1e-1)
        
if __name__ == '__main__':
    unittest.main()